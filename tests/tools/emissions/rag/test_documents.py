"""Tests for reading, filtering and fingerprinting the SCC table."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from config.retrieval import load_embedding_settings, load_scc_index_settings
from tests.tools.emissions.rag.fakes import HEADER, INDEXED, ROWS, scc_settings
from tools.emissions.rag.documents import SccDocument, fingerprint, load_documents
from tools.emissions.rag.errors import SourceError


def test_point_active_only_deduped(tmp_path: Path) -> None:
    documents = load_documents(scc_settings(tmp_path))
    assert tuple(d.scc for d in documents) == INDEXED
    first = documents[0]
    assert first.level_four == "Catalytic Cracking Unit"  # first row of a duplicate SCC wins
    assert first.sector == "Industrial Processes - Petroleum Refineries"


def test_other_filters_from_settings(tmp_path: Path) -> None:
    settings = scc_settings(tmp_path, statuses=("Active", "Retired"), categories=("Point",))
    assert "99900003" in {d.scc for d in load_documents(settings)}


def test_document_text_and_metadata_round_trip(tmp_path: Path) -> None:
    document = load_documents(scc_settings(tmp_path))[0]
    assert document.text() == (
        "Industrial Processes > Petroleum Industry > Petroleum Refining > "
        "Catalytic Cracking Unit (sector: Industrial Processes - Petroleum Refineries)"
    )
    indexed = document.to_indexed()
    assert indexed.id == "99900001"
    assert SccDocument.from_metadata(indexed.id, indexed.metadata) == document


@pytest.mark.parametrize("drop", ["level_four", "sector"])
def test_incomplete_metadata_rejected(tmp_path: Path, drop: str) -> None:
    metadata = dict(load_documents(scc_settings(tmp_path))[0].metadata())
    del metadata[drop]
    assert SccDocument.from_metadata("1", metadata) is None


def test_blank_level_four_metadata_rejected(tmp_path: Path) -> None:
    metadata = {**load_documents(scc_settings(tmp_path))[0].metadata(), "level_four": ""}
    assert SccDocument.from_metadata("1", metadata) is None


def test_missing_table_is_source_error(tmp_path: Path) -> None:
    settings = scc_settings(tmp_path)
    settings.source_path.unlink()
    with pytest.raises(SourceError, match="could not be read"):
        load_documents(settings)
    with pytest.raises(SourceError, match="could not be read"):
        fingerprint(settings, load_embedding_settings())


def test_no_matching_rows_is_source_error(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="no SCC rows match"):
        load_documents(scc_settings(tmp_path, categories=("Onroad",)))


def test_missing_configured_column_raises(tmp_path: Path) -> None:
    settings = scc_settings(tmp_path, HEADER.replace('"sector"', '"sectors"') + ROWS)
    with pytest.raises(ValueError, match="lacks configured columns: sector"):
        load_documents(settings)


def test_fingerprint_tracks_content_and_settings(tmp_path: Path) -> None:
    settings = scc_settings(tmp_path)
    embedding = load_embedding_settings()
    base = fingerprint(settings, embedding)
    assert fingerprint(settings, embedding) == base
    assert fingerprint(replace(settings, statuses=("Retired",)), embedding) != base
    assert fingerprint(settings, replace(embedding, model="other-model")) != base
    settings.source_path.write_text(HEADER + ROWS.replace("Coal Boiler", "Gas Boiler"))
    assert fingerprint(settings, embedding) != base


def test_real_table_is_indexable() -> None:
    """The bundled table matches the configured columns and yields unique Point/Active SCCs."""
    documents = load_documents(load_scc_index_settings())
    sccs = [d.scc for d in documents]
    assert len(sccs) == len(set(sccs)) > 1000
    assert all(d.level_four for d in documents)
