"""Tests for the embeddings provider factory and its guard."""

from __future__ import annotations

import openai
import pytest
from langchain_core.embeddings import Embeddings

from config.retrieval import SUPPORTED_EMBEDDING_PROVIDERS, load_embedding_settings
from tools.emissions.rag.embeddings import GuardedEmbeddings, build_embeddings, supported_providers
from tools.emissions.rag.errors import EmbeddingError


class _Stub(Embeddings):
    def __init__(
        self, documents: object = None, query: object = None, error: Exception | None = None
    ) -> None:
        self._documents = documents
        self._query = query
        self._error = error

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._error:
            raise self._error
        return self._documents  # type: ignore[return-value]

    def embed_query(self, text: str) -> list[float]:
        if self._error:
            raise self._error
        return self._query  # type: ignore[return-value]


ERRORS: tuple[type[Exception], ...] = (openai.OpenAIError,)


def test_registry_matches_config() -> None:
    assert supported_providers() == SUPPORTED_EMBEDDING_PROVIDERS


@pytest.mark.parametrize("environ", [{}, {"OPENAI_API_KEY": "  "}])
def test_missing_key_raises_without_building(environ: dict[str, str]) -> None:
    with pytest.raises(EmbeddingError, match="OPENAI_API_KEY is not set"):
        build_embeddings(load_embedding_settings(), environ)


def test_builds_guarded_openai_without_network() -> None:
    environ = {"OPENAI_API_KEY": "test-key"}  # pragma: allowlist secret
    embeddings = build_embeddings(load_embedding_settings(), environ)
    assert isinstance(embeddings, GuardedEmbeddings)


def test_valid_vectors_returned_as_copies() -> None:
    source = [[0.5, 1]]
    guarded = GuardedEmbeddings(_Stub(documents=source, query=[1, 2.5]), ERRORS)
    vectors = guarded.embed_documents(["a"])
    assert vectors == [[0.5, 1.0]]
    assert vectors[0] is not source[0]
    assert guarded.embed_query("a") == [1.0, 2.5]


@pytest.mark.parametrize(
    "error",
    [openai.OpenAIError("connection reset"), openai.OpenAIError("request timed out")],
)
def test_provider_errors_become_embedding_error(error: Exception) -> None:
    guarded = GuardedEmbeddings(_Stub(error=error), ERRORS)
    with pytest.raises(EmbeddingError, match="embedding request failed"):
        guarded.embed_documents(["a"])
    with pytest.raises(EmbeddingError, match="embedding request failed"):
        guarded.embed_query("a")


def test_unexpected_errors_propagate() -> None:
    guarded = GuardedEmbeddings(_Stub(error=KeyError("bug")), ERRORS)
    with pytest.raises(KeyError):
        guarded.embed_query("a")


@pytest.mark.parametrize(
    "documents",
    [
        [[1.0]],  # two texts sent, one vector back
        [[1.0], []],
        [[1.0], [float("nan")]],
        [[1.0], [float("inf")]],
        [[1.0], [True]],
        [[1.0], ["1"]],
        None,
    ],
)
def test_malformed_vectors_rejected(documents: object) -> None:
    guarded = GuardedEmbeddings(_Stub(documents=documents), ERRORS)
    with pytest.raises(EmbeddingError):
        guarded.embed_documents(["a", "b"])


def test_malformed_query_vector_rejected() -> None:
    guarded = GuardedEmbeddings(_Stub(query=[]), ERRORS)
    with pytest.raises(EmbeddingError):
        guarded.embed_query("a")
