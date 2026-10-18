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


def test_gzip_table_gives_the_same_documents(tmp_path: Path) -> None:
    import gzip

    plain = scc_settings(tmp_path)
    packed = tmp_path / "scc.csv.gz"
    packed.write_bytes(gzip.compress((HEADER + ROWS).encode("utf-8")))
    assert load_documents(replace(plain, source_path=packed)) == load_documents(plain)


def test_gzip_table_fingerprint_follows_its_bytes(tmp_path: Path) -> None:
    import gzip

    settings = scc_settings(tmp_path)
    packed = tmp_path / "scc.csv.gz"
    packed.write_bytes(gzip.compress((HEADER + ROWS).encode("utf-8")))
    embedding = load_embedding_settings()
    same = replace(settings, source_path=packed)
    assert fingerprint(same, embedding) == fingerprint(same, embedding)
    assert fingerprint(same, embedding) != fingerprint(settings, embedding)


@pytest.mark.parametrize("content", [b"not gzip at all", b"\x1f\x8b\x08\x00truncated"])
def test_bad_gzip_table_is_a_source_error(tmp_path: Path, content: bytes) -> None:
    bad = tmp_path / "scc.csv.gz"
    bad.write_bytes(content)
    with pytest.raises(SourceError, match="could not be read"):
        load_documents(replace(scc_settings(tmp_path), source_path=bad))


@pytest.mark.parametrize("name", ["table.csv", "table.csv.gz"])
def test_empty_table_lacks_columns_plain_or_gzip(tmp_path: Path, name: str) -> None:
    settings = scc_settings(tmp_path)  # writes tmp_path/scc.csv: use another file for the test
    empty = tmp_path / f"empty-{name}"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="lacks configured columns"):
        load_documents(replace(settings, source_path=empty))
