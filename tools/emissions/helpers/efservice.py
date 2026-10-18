"""Throttled, retrying access to EPA Envirofacts (``efservice``) JSON queries."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

import httpx

from config.efservice import EfserviceSettings

logger = logging.getLogger(__name__)

Row = Mapping[str, object]
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class EfserviceError(RuntimeError):
    """A request could not be completed; no partial result should be used."""


@dataclass(frozen=True)
class _Retry:
    """A failed attempt worth repeating, with the server's requested wait if it gave one."""

    reason: str
    wait: float | None = None


def _retry_after(response: httpx.Response) -> float | None:
    """Return the ``Retry-After`` header as seconds if it is a non-negative number."""
    raw = response.headers.get("Retry-After", "").strip()
    try:
        seconds = float(raw)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _rows(payload: object) -> list[Row] | None:
    """Return the rows of a JSON list of objects, or None if it has any other shape."""
    if not isinstance(payload, list):
        return None
    items = cast(list[object], payload)
    if not all(isinstance(item, dict) for item in items):
        return None
    return [{str(k): v for k, v in cast(dict[object, object], item).items()} for item in items]


class EfserviceClient:
    """Fetches Envirofacts queries one at a time, politely.

    Every request waits the configured delay first. Throttling (HTTP 429), server errors and
    timeouts are retried a configured number of times with a doubling wait (``Retry-After`` is
    honoured, up to the request timeout); anything else that is not a list of rows fails.
    """

    def __init__(
        self,
        settings: EfserviceSettings,
        client: httpx.Client,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a client.

        Args:
            settings: Base URL, delay, timeout and retry policy.
            client: HTTP client (injectable for tests).
            sleep: Function used to wait; replaced in tests.
        """
        self._settings = settings
        self._client = client
        self._sleep = sleep

    def get_rows(self, path: str) -> list[Row]:
        """Return the rows of one query.

        Args:
            path: Query path starting with ``/``, appended to the configured base URL.

        Raises:
            EfserviceError: If the request still fails after the configured retries, or the
                response is not a list of JSON objects.
        """
        url = self._settings.url(path)
        retries = self._settings.max_retries
        reason = ""
        for attempt in range(retries + 1):
            self._sleep(self._settings.delay_seconds)
            outcome = self._attempt(url)
            if isinstance(outcome, list):
                return outcome
            reason = outcome.reason
            logger.debug("Envirofacts request failed (%s), attempt %d", reason, attempt + 1)
            if attempt < retries:
                self._sleep(self._wait(attempt, outcome))
        raise EfserviceError(f"Envirofacts request failed after {retries + 1} attempts: {reason}")

    def _wait(self, attempt: int, retry: _Retry) -> float:
        backoff = self._settings.backoff_seconds * 2**attempt
        if retry.wait is None:
            return backoff
        return min(retry.wait, self._settings.timeout_seconds)

    def _attempt(self, url: str) -> list[Row] | _Retry:
        try:
            response = self._client.get(url, timeout=self._settings.timeout_seconds)
        except httpx.HTTPError as exc:
            return _Retry(f"{type(exc).__name__}")
        if response.status_code in _RETRYABLE_STATUS:
            return _Retry(f"HTTP {response.status_code}", _retry_after(response))
        if response.status_code != 200:
            raise EfserviceError(f"Envirofacts returned HTTP {response.status_code}")
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> list[Row] | _Retry:
        try:
            payload = cast(object, response.json())
        except ValueError:
            return _Retry("malformed JSON")
        rows = _rows(payload)
        if rows is None:
            raise EfserviceError("Envirofacts response is not a list of objects")
        return rows
