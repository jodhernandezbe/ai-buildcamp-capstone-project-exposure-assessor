"""Tests for lookup_scc_process_description."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.retrieval import load_embedding_settings
from tests.tools.emissions.rag.fakes import KeywordEmbeddings, scc_settings
from tools.emissions import process
from tools.emissions.process import lookup_scc_process_description
from tools.emissions.rag.errors import EmbeddingError
from tools.emissions.rag.retriever import SccRetriever


@pytest.fixture
def fake_retriever(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> KeywordEmbeddings:
    embeddings = KeywordEmbeddings()
    retriever = SccRetriever(scc_settings(tmp_path, top_k=2), load_embedding_settings(), embeddings)
    monkeypatch.setattr(process, "_get_retriever", lambda: retriever)
    return embeddings


def test_schema_and_description() -> None:
    tool = lookup_scc_process_description
    assert tool.name == "lookup_scc_process_description"
    assert set(tool.args) == {"naics_description"}
    for text in ("level four", "fetch_stack_parameters_from_scc", "not an official", "score"):
        assert text in tool.description


@pytest.mark.usefixtures("fake_retriever")
def test_matches_mapped_best_first() -> None:
    result = lookup_scc_process_description.invoke({"naics_description": "Petroleum Refineries"})
    assert result["warnings"] == []
    assert len(result["matches"]) == 2
    best = result["matches"][0]
    assert best == {
        "scc": "99900001",
        "level_one": "Industrial Processes",
        "level_two": "Petroleum Industry",
        "level_three": "Petroleum Refining",
        "level_four": "Catalytic Cracking Unit",
        "sector": "Industrial Processes - Petroleum Refineries",
        "score": best["score"],
    }
    assert 0.0 <= result["matches"][1]["score"] <= best["score"] <= 1.0


def test_empty_description_warns(fake_retriever: KeywordEmbeddings) -> None:
    result = lookup_scc_process_description.invoke({"naics_description": " "})
    assert result == {"matches": [], "warnings": ["the industry description is empty"]}
    assert fake_retriever.query_calls == 0


def test_missing_key_is_a_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable() -> SccRetriever:
        raise EmbeddingError("OPENAI_API_KEY is not set")

    monkeypatch.setattr(process, "_get_retriever", unavailable)
    result = lookup_scc_process_description.invoke({"naics_description": "Refineries"})
    assert result == {
        "matches": [],
        "warnings": ["SCC lookup unavailable: OPENAI_API_KEY is not set"],
    }
