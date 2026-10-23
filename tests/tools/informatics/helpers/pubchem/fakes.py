"""Shared test doubles for the PubChem client (no network)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from config.pubchem import CacheSettings, PubchemSettings, get_pubchem_settings
from tools.http import HttpRequestError


class FakeClock:
    """A settable clock."""

    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


@dataclass
class FakeJson:
    """A JSON getter answering from a url -> payload table; an exception value is raised."""

    answers: Mapping[str, object]
    calls: list[str] = field(default_factory=lambda: [])

    def get_json(self, url: str, params: Mapping[str, str | int | float] | None = None) -> object:
        self.calls.append(url)
        if url not in self.answers:
            raise HttpRequestError("server returned HTTP 404", 404)
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        return answer


def settings_in(directory: Path, enabled: bool = True) -> PubchemSettings:
    """The shipped settings with the cache moved into ``directory``."""
    base = get_pubchem_settings()
    cache = CacheSettings(enabled, directory / "cache.sqlite", base.cache.ttl_days)
    return replace(base, cache=cache)


def sleeper() -> tuple[list[float], Callable[[float], None]]:
    """A recording replacement for ``time.sleep``."""
    waits: list[float] = []
    return waits, waits.append
