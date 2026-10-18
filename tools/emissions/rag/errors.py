"""Errors raised inside the SCC retrieval; callers turn them into warnings."""

from __future__ import annotations


class RetrievalError(RuntimeError):
    """Base class for expected retrieval failures (data or service problems)."""


class EmbeddingError(RetrievalError):
    """The embedding provider is unavailable, failed, timed out or returned bad vectors."""


class VectorStoreError(RetrievalError):
    """The persisted vector index could not be opened, built or queried."""


class SourceError(RetrievalError):
    """The source corpus could not be read or yielded no documents."""
