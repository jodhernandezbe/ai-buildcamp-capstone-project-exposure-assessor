"""Throttled, retrying access to EPA Envirofacts (``efservice``) JSON queries."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import cast

import httpx

from config.efservice import EfserviceSettings
from tools.http import HttpRequestError, RetryingClient

Row = Mapping[str, object]


class EfserviceError(RuntimeError):
    """A request could not be completed; no partial result should be used."""


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

    Throttling, retries and timeouts are the shared ``RetryingClient``'s; an answer that is
    not a list of JSON objects fails the lookup.
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
        self._http = RetryingClient(settings, client, sleep)

    def get_rows(self, path: str) -> list[Row]:
        """Return the rows of one query.

        Args:
            path: Query path starting with ``/``, appended to the configured base URL.

        Raises:
            EfserviceError: If the request still fails after the configured retries, or the
                response is not a list of JSON objects.
        """
        try:
            payload = self._http.get_json(self._settings.url(path))
        except HttpRequestError as exc:
            raise EfserviceError(f"Envirofacts {exc}") from exc
        rows = _rows(payload)
        if rows is None:
            raise EfserviceError("Envirofacts response is not a list of objects")
        return rows
