"""Throttled, retrying, cached JSON GET for PubChem."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

import httpx

from config.pubchem import PubchemSettings
from tools.http import HttpRequestError, RetryingClient
from tools.informatics.helpers.pubchem.cache import ResponseCache

_NOT_FOUND = 404


class JsonGetter(Protocol):
    """Anything that returns the decoded JSON of a GET (``RetryingClient``, the cached client)."""

    def get_json(self, url: str) -> object:
        """Return the decoded JSON body of a GET request."""
        ...


class CachedJsonClient:
    """A JSON client that answers from the cache when it can.

    A cached "not found" raises the same ``HttpRequestError`` (status 404) as a live one, so a
    caller cannot tell a cached answer from a live one. Failures are never cached.
    """

    def __init__(self, inner: JsonGetter, cache: ResponseCache | None) -> None:
        """Create the client.

        Args:
            inner: The throttled, retrying client that asks PubChem.
            cache: The response cache, or None for no caching.
        """
        self._inner = inner
        self._cache = cache

    def get_json(self, url: str) -> object:
        """Return the decoded JSON of ``url``.

        Raises:
            HttpRequestError: If PubChem has nothing (status 404, possibly cached) or the
                request failed after the configured retries.
        """
        cached = self._cache.get(url) if self._cache else None
        if cached is not None:
            if cached.status == _NOT_FOUND:
                raise HttpRequestError("server returned HTTP 404 (cached)", _NOT_FOUND)
            return cached.payload
        return self._fetch(url)

    def _fetch(self, url: str) -> object:
        try:
            payload = self._inner.get_json(url)
        except HttpRequestError as exc:
            if exc.status_code == _NOT_FOUND and self._cache:
                self._cache.put_not_found(url)
            raise
        if self._cache:
            self._cache.put_ok(url, payload)
        return payload


def build_client(
    settings: PubchemSettings,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
    transport: httpx.BaseTransport | None = None,
) -> CachedJsonClient:
    """Build the default PubChem client (the outer edge; tests inject their own).

    Args:
        settings: URLs' request policy (delay, timeout, retries), user agent and cache.
        sleep: Function used to wait; replaced in tests.
        clock: Seconds since the epoch for the cache; replaced in tests.
        transport: HTTP transport; replaced in tests by a mock.
    """
    http = httpx.Client(headers={"User-Agent": settings.user_agent}, transport=transport)
    cache = settings.cache
    store = ResponseCache(cache.path, cache.ttl_days, clock) if cache.enabled else None
    return CachedJsonClient(RetryingClient(settings, http, sleep), store)
