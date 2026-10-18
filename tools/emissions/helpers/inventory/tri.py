"""Paged retrieval of TRI release rows from EPA Envirofacts."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from urllib.parse import quote

from config.loader import TriSettings
from tools.emissions.helpers.efservice import EfserviceClient, Row


class TriFetcher:
    """Reads the TRI release rows of one chemical and medium, a page at a time.

    Pages are requested one after another, never concurrently; throttling, retries and
    timeouts are the shared Envirofacts client's.
    """

    def __init__(self, settings: TriSettings, client: EfserviceClient, current_year: int) -> None:
        """Create a fetcher.

        Args:
            settings: TRI settings (query path, paging).
            client: Envirofacts client (injectable for tests).
            current_year: The current calendar year; the window of recent reporting years ends
                with it.
        """
        self._settings = settings
        self._client = client
        self._after_year = settings.after_year(current_year)

    def fetch(
        self,
        cas: str,
        medium: str,
        consume: Callable[[Sequence[Row]], None],
    ) -> bool:
        """Fetch every page for a chemical and medium, handing each to ``consume``.

        Args:
            cas: Hyphenated CAS registry number, already validated.
            medium: TRI environmental medium, e.g. "AIR STACK".
            consume: Called with the rows of each page as soon as it arrives.

        Returns:
            True if the page cap was reached before a short page, i.e. the result may be
            incomplete; False when the last page was short.

        Raises:
            EfserviceError: If a page still fails after the configured retries, or the
                response is not a list of objects.
        """
        size = self._settings.page_size
        for page in range(self._settings.max_pages):
            rows = self._client.get_rows(self._path(cas, medium, page * size))
            consume(rows)
            if len(rows) < size:
                return False
        return True

    def _path(self, cas: str, medium: str, start: int) -> str:
        return self._settings.release_path.format(
            casrn=quote(cas, safe=""),
            medium=quote(medium, safe=""),
            start=start,
            end=start + self._settings.page_size - 1,
            after_year=self._after_year,
        )
