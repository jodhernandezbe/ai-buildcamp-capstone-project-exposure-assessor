"""Test doubles for the SCC retrieval: a keyword embedder and a synthetic SCC table.

The table uses obviously fake SCCs (999...) and generic process wording, not real SCC rows.
"""

from __future__ import annotations

import math
import re
import zlib
from dataclasses import replace
from pathlib import Path

from langchain_core.embeddings import Embeddings

from config.retrieval import SccIndexSettings, load_scc_index_settings

HEADER = (
    '"SCC","data category","status","scc level one","scc level two","scc level three",'
    '"scc level four","sector"\n'
)
ROWS = (
    '"99900001","Point","Active","Industrial Processes","Petroleum Industry",'
    '"Petroleum Refining","Catalytic Cracking Unit","Industrial Processes - Petroleum Refineries"\n'
    '"99900002","Point","Active","External Combustion","Electric Generation",'
    '"Coal","Pulverized Coal Boiler","Fuel Comb - Electric Generation - Coal"\n'
    '"99900003","Point","Retired","Industrial Processes","Petroleum Industry",'
    '"Petroleum Refining","Retired Refining Unit","Industrial Processes - Petroleum Refineries"\n'
    '"99900004","Nonpoint","Active","Industrial Processes","Petroleum Industry",'
    '"Petroleum Refining","Area Refining Source","Industrial Processes - Petroleum Refineries"\n'
    '"99900001","Point","Active","Duplicate","Duplicate","Duplicate","Duplicate","Duplicate"\n'
    '"99900005","Point","Active","Industrial Processes","Chemical Manufacturing",'
    '"Organic Chemicals","","Industrial Processes - Chemical Manufacturing"\n'
    '"","Point","Active","Industrial Processes","Chemical Manufacturing",'
    '"Organic Chemicals","No Code","Industrial Processes - Chemical Manufacturing"\n'
    '"99900006","Point","Active","Industrial Processes","Chemical Manufacturing",'
    '"Organic Chemicals","Formaldehyde Production Reactor",'
    '"Industrial Processes - Chemical Manufacturing"\n'
)
# SCCs that pass the Point/Active filter with an SCC and a level four description.
INDEXED = ("99900001", "99900002", "99900006")


class KeywordEmbeddings(Embeddings):
    """Deterministic bag-of-words vectors (hashed into 64 buckets); counts its calls."""

    def __init__(self, fail_after_documents: int | None = None) -> None:
        self.document_calls = 0
        self.query_calls = 0
        self.fail_after_documents = fail_after_documents
        self.error: Exception = RuntimeError("provider down")

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0] * 64
        for word in re.findall(r"[a-z]+", text.lower()):
            vector[zlib.crc32(word.encode()) % 64] += 1.0
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector] if any(vector) else [1.0] + [0.0] * 63

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if (
            self.fail_after_documents is not None
            and self.document_calls >= self.fail_after_documents
        ):
            raise self.error
        self.document_calls += 1
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        self.query_calls += 1
        return self._vector(text)


def scc_settings(tmp_path: Path, text: str = HEADER + ROWS, **changes: object) -> SccIndexSettings:
    """Default settings pointed at a synthetic table and a temporary index directory."""
    source = tmp_path / "scc.csv"
    source.write_text(text)
    base = replace(
        load_scc_index_settings(),
        source_path=source,
        persist_dir=tmp_path / "index",
        collection="scc_test",
        batch_size=2,
    )
    return replace(base, **changes)  # type: ignore[arg-type]
