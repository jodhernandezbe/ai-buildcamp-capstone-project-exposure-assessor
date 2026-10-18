"""Public entry point of the SCC retrieval: ``SccRetriever`` and its default instance."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import cast

from langchain_core.embeddings import Embeddings

from config.retrieval import (
    EmbeddingSettings,
    SccIndexSettings,
    get_embedding_settings,
    get_scc_index_settings,
)
from tools.emissions.rag.documents import SccHit, fingerprint, load_documents
from tools.emissions.rag.embeddings import build_embeddings
from tools.emissions.rag.graph import SccGraph, SccState, build_scc_graph
from tools.emissions.rag.vectorstore import IndexedDocument, VectorIndex


@dataclass(frozen=True)
class SccLookup:
    """Retrieved SCCs, best first, and warnings explaining anything missing."""

    hits: tuple[SccHit, ...]
    warnings: tuple[str, ...]


class SccRetriever:
    """Finds SCC process descriptions similar to an industry (NAICS) description."""

    def __init__(
        self, settings: SccIndexSettings, embedding: EmbeddingSettings, embeddings: Embeddings
    ) -> None:
        """Args: index settings, embedding settings (for the fingerprint), embeddings."""
        index = VectorIndex(
            settings.persist_dir, settings.collection, embeddings, settings.batch_size
        )
        self._graph: SccGraph = build_scc_graph(
            index,
            settings.top_k,
            fingerprint=lambda: fingerprint(settings, embedding),
            load=lambda: _indexed(settings),
        )

    def lookup(self, description: str) -> SccLookup:
        """Return up to ``top_k`` SCCs for ``description``; failures become warnings.

        Raises:
            ValueError: If the SCC table lacks a configured column (a setup error).
        """
        start = SccState(query=description, hits=[], warnings=[], failed=False)
        state = cast(SccState, self._graph.invoke(start))
        return SccLookup(hits=tuple(state["hits"]), warnings=tuple(state["warnings"]))


def _indexed(settings: SccIndexSettings) -> list[IndexedDocument]:
    return [document.to_indexed() for document in load_documents(settings)]


@lru_cache(maxsize=1)
def default_scc_retriever() -> SccRetriever:
    """Build the retriever from the default settings and provider (the outer edge).

    Only a successful build is cached, so setting a missing API key later takes effect.

    Raises:
        EmbeddingError: If the provider API key is not set.
    """
    embedding = get_embedding_settings()
    return SccRetriever(get_scc_index_settings(), embedding, build_embeddings(embedding))
