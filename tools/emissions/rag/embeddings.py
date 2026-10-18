"""Embedding provider factory: the only module that imports a provider package.

Everything else in this package works with ``langchain_core.embeddings.Embeddings``,
so changing provider means adding an entry to ``_PROVIDERS`` (and to
``config.retrieval.SUPPORTED_EMBEDDING_PROVIDERS``) and editing ``[embeddings]`` in
``config/settings.toml``.
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from langchain_core.embeddings import Embeddings
from pydantic import SecretStr

from config.retrieval import EmbeddingSettings
from tools.emissions.rag.errors import EmbeddingError


@dataclass(frozen=True)
class _Provider:
    """How to build one provider's embeddings and which of its exceptions are expected."""

    build: Callable[[EmbeddingSettings, str], Embeddings]
    errors: Callable[[], tuple[type[Exception], ...]]


def _openai_embeddings(settings: EmbeddingSettings, api_key: str) -> Embeddings:
    from langchain_openai import OpenAIEmbeddings  # provider package: imported only here

    return OpenAIEmbeddings(
        model=settings.model,
        api_key=SecretStr(api_key),
        timeout=settings.timeout_seconds,
        max_retries=1,
        # Inputs are short descriptions; skip tiktoken length checks (and their download).
        check_embedding_ctx_length=False,
    )


def _openai_errors() -> tuple[type[Exception], ...]:
    import openai

    # The SDK wraps every transport failure (timeouts, connection errors) in OpenAIError.
    return (openai.OpenAIError,)


_PROVIDERS: Mapping[str, _Provider] = {
    "openai": _Provider(build=_openai_embeddings, errors=_openai_errors),
}


def _is_finite_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int | float) and math.isfinite(value)


def _check_vector(vector: object) -> list[float]:
    """Return a copy of ``vector`` if it is a non-empty list of finite numbers."""
    items = cast(list[object], vector) if isinstance(vector, list) else []
    if not items or not all(_is_finite_number(x) for x in items):
        raise EmbeddingError("provider returned an empty or non-finite vector")
    return [float(cast(float, x)) for x in items]


def _check_vectors(vectors: object, expected: int) -> list[list[float]]:
    """Return copies of the provider output if it is ``expected`` valid vectors."""
    items = cast(list[object], vectors) if isinstance(vectors, list) else None
    if items is None or len(items) != expected:
        raise EmbeddingError(f"provider returned an unexpected number of vectors ({expected} sent)")
    return [_check_vector(vector) for vector in items]


class GuardedEmbeddings(Embeddings):
    """Wrap a provider: its expected errors become ``EmbeddingError``; outputs are validated."""

    def __init__(self, inner: Embeddings, errors: tuple[type[Exception], ...]) -> None:
        self._inner = inner
        self._errors = errors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed ``texts``; raises ``EmbeddingError`` on provider failure or bad output."""
        try:
            vectors = self._inner.embed_documents(texts)
        except self._errors as exc:
            raise EmbeddingError(f"embedding request failed ({type(exc).__name__})") from exc
        return _check_vectors(vectors, len(texts))

    def embed_query(self, text: str) -> list[float]:
        """Embed one query; raises ``EmbeddingError`` on provider failure or bad output."""
        try:
            vector = self._inner.embed_query(text)
        except self._errors as exc:
            raise EmbeddingError(f"embedding request failed ({type(exc).__name__})") from exc
        return _check_vectors([vector], 1)[0]


def build_embeddings(
    settings: EmbeddingSettings, environ: Mapping[str, str] | None = None
) -> Embeddings:
    """Build the configured provider's embeddings (the outer edge for this collaborator).

    Args:
        settings: Provider, model, API-key variable name and timeout (seconds).
        environ: Environment the API key is read from; defaults to ``os.environ``.

    Returns:
        Guarded embeddings: provider failures surface as ``EmbeddingError``.

    Raises:
        EmbeddingError: If the API-key environment variable is unset or blank.
        ValueError: If the provider is not supported (a configuration error).
    """
    env = os.environ if environ is None else environ
    api_key = env.get(settings.api_key_env_var, "").strip()
    if not api_key:
        raise EmbeddingError(f"{settings.api_key_env_var} is not set")
    provider = _PROVIDERS.get(settings.provider)
    if provider is None:
        raise ValueError(f"unsupported embedding provider: {settings.provider}")
    return GuardedEmbeddings(provider.build(settings, api_key), provider.errors())


def supported_providers() -> tuple[str, ...]:
    """Names of the providers this module can build."""
    return tuple(_PROVIDERS)
