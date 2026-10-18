"""Persistent vector index (Chroma) that rebuilds itself when its source changes.

The only module that imports ``chromadb``. Vectors come from an injected
``langchain_core.embeddings.Embeddings``, so Chroma's own default embedder is never used
(nor downloaded). The collection metadata records the source fingerprint and the number of
documents written, so a stale or half-built index is never reused.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import chromadb
import numpy as np
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.api.types import QueryResult
from chromadb.config import Settings
from chromadb.errors import ChromaError
from langchain_core.embeddings import Embeddings

from tools.emissions.rag.errors import VectorStoreError

_FINGERPRINT_KEY = "fingerprint"
_COUNT_KEY = "expected_count"
_STORE_ERRORS = (ChromaError, sqlite3.Error, OSError)


@dataclass(frozen=True)
class IndexedDocument:
    """One document to index: unique ``id``, the ``text`` embedded, string ``metadata``."""

    id: str
    text: str
    metadata: Mapping[str, str]


@dataclass(frozen=True)
class ScoredDocument:
    """One query hit: document ``id``, its stored ``metadata`` and a similarity ``score``.

    ``score`` is 1 - cosine distance, clipped to [0, 1] (1 = same direction).
    """

    id: str
    metadata: Mapping[str, str]
    score: float


def _string_metadata(raw: Mapping[str, object] | None) -> Mapping[str, str]:
    return MappingProxyType({k: v for k, v in (raw or {}).items() if isinstance(v, str)})


def _scored(result: QueryResult) -> list[ScoredDocument]:
    """Turn Chroma's per-query lists (first query only) into scored hits."""
    ids = result["ids"][0] if result["ids"] else []
    metadatas = (result["metadatas"] or [[]])[0]
    distances = (result["distances"] or [[]])[0]
    return [
        ScoredDocument(id=i, metadata=_string_metadata(m), score=max(0.0, min(1.0, 1.0 - d)))
        for i, m, d in zip(ids, metadatas, distances, strict=True)
    ]


class VectorIndex:
    """A named, persisted collection of embedded documents."""

    def __init__(
        self, persist_dir: Path, collection: str, embeddings: Embeddings, batch_size: int
    ) -> None:
        """Args: index directory, collection name, embeddings (injected), docs per request."""
        self._persist_dir = persist_dir
        self._name = collection
        self._embeddings = embeddings
        self._batch_size = batch_size
        self._client: ClientAPI | None = None
        self._ready_fingerprint: str | None = None

    def _open(self) -> ClientAPI:
        if self._client is None:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            settings = Settings(anonymized_telemetry=False)
            self._client = chromadb.PersistentClient(path=str(self._persist_dir), settings=settings)
        return self._client

    def _is_current(self, fingerprint: str) -> bool:
        collection = self._open().get_or_create_collection(self._name, embedding_function=None)
        metadata = collection.metadata or {}
        expected = metadata.get(_COUNT_KEY)
        return metadata.get(_FINGERPRINT_KEY) == fingerprint and collection.count() == expected

    def _add(self, collection: Collection, batch: Sequence[IndexedDocument]) -> None:
        vectors = self._embeddings.embed_documents([d.text for d in batch])
        collection.add(
            ids=[d.id for d in batch],
            embeddings=np.asarray(vectors, dtype=np.float32),
            documents=[d.text for d in batch],
            metadatas=[dict(d.metadata) for d in batch],
        )

    def _rebuild(self, fingerprint: str, documents: Sequence[IndexedDocument]) -> None:
        client = self._open()
        client.delete_collection(self._name)
        collection = client.create_collection(
            self._name,
            metadata={_FINGERPRINT_KEY: fingerprint, _COUNT_KEY: len(documents)},
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )
        for start in range(0, len(documents), self._batch_size):
            self._add(collection, documents[start : start + self._batch_size])

    def ensure(self, fingerprint: str, load: Callable[[], Sequence[IndexedDocument]]) -> bool:
        """Make the index match ``fingerprint``, rebuilding it from ``load()`` if needed.

        Returns:
            True if the index was (re)built, False if the persisted one was reused.

        Raises:
            VectorStoreError: If the store cannot be opened or written.
            Whatever ``load`` or the embeddings raise (e.g. ``SourceError``,
            ``EmbeddingError``); a half-built index is detected and rebuilt next time.
        """
        if self._ready_fingerprint == fingerprint:
            return False
        try:
            current = self._is_current(fingerprint)
            if not current:
                self._rebuild(fingerprint, load())
        except _STORE_ERRORS as exc:
            raise VectorStoreError(f"vector index {self._name} failed: {exc}") from exc
        self._ready_fingerprint = fingerprint
        return not current

    def query(self, text: str, k: int) -> list[ScoredDocument]:
        """Return up to ``k`` documents most similar to ``text``, best first.

        Raises:
            VectorStoreError: If the store cannot be queried.
            EmbeddingError: If the query cannot be embedded.
        """
        vector = self._embeddings.embed_query(text)
        try:
            collection = self._open().get_collection(self._name, embedding_function=None)
            result = collection.query(
                query_embeddings=[vector], n_results=k, include=["metadatas", "distances"]
            )
        except _STORE_ERRORS as exc:
            raise VectorStoreError(f"vector index {self._name} query failed: {exc}") from exc
        return _scored(result)
