"""Tests for tools.emissions.helpers.lookup."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from config.efservice import load_efservice_settings
from config.loader import EmissionsSettings, TriSettings, get_unit_settings, load_tri_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.lookup import lookup_emissions
from tools.emissions.helpers.tri import TriFetcher
from tools.schemas import EmissionRecord

ROWS = json.loads(Path(__file__).with_name("tri_rows.json").read_text())
SETTINGS = replace(load_tri_settings(), page_size=4, max_pages=3)
EMISSIONS = EmissionsSettings(8760.0)
CAS = "50-00-0"


def _fetcher(transport: httpx.MockTransport, settings: TriSettings = SETTINGS) -> TriFetcher:
    client = EfserviceClient(
        load_efservice_settings(), httpx.Client(transport=transport), lambda _seconds: None
    )
    return TriFetcher(settings, client)


def _serve(pages: Sequence[Sequence[Mapping[str, object]]]) -> httpx.MockTransport:
    queue = list(pages)
    return httpx.MockTransport(lambda request: httpx.Response(200, json=queue.pop(0)))


def _lookup(fetcher: TriFetcher, settings: TriSettings = SETTINGS) -> list[EmissionRecord]:
    return lookup_emissions(CAS, settings, EMISSIONS, get_unit_settings().aliases, fetcher)


def test_rows_across_pages_are_reduced() -> None:
    fetcher = _fetcher(_serve([ROWS[:4], ROWS[4:]]))
    records = _lookup(fetcher)
    assert {r["frs_id"] for r in records} == {"110000307864", "110021074834"}


def test_nothing_reported_gives_empty_list() -> None:
    assert _lookup(_fetcher(_serve([[]]))) == []


def test_each_configured_medium_is_queried() -> None:
    settings = replace(SETTINGS, media=("AIR STACK", "AIR FUGITIVE"))
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json=[])

    _lookup(_fetcher(httpx.MockTransport(handler), settings), settings)
    assert [("AIR%20STACK" in u, "AIR%20FUGITIVE" in u) for u in urls] == [
        (True, False),
        (False, True),
    ]


def test_failure_returns_empty_not_partial(caplog: pytest.LogCaptureFixture) -> None:
    answers = [httpx.Response(200, json=ROWS[:4])] + [httpx.Response(500)] * 3
    transport = httpx.MockTransport(lambda request: answers.pop(0))
    with caplog.at_level(logging.WARNING):
        records = _lookup(_fetcher(transport))
    assert records == []
    assert "failed" in caplog.text


def test_page_cap_is_warned(caplog: pytest.LogCaptureFixture) -> None:
    full = [{**ROWS[0], "epa_registry_id": f"F{i}"} for i in range(4)]
    with caplog.at_level(logging.WARNING):
        records = _lookup(_fetcher(_serve([full, full, full])))
    assert len(records) == 4
    assert "page cap" in caplog.text


def test_data_warnings_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        _lookup(_fetcher(_serve([ROWS[:4], ROWS[4:]])))
    assert "no usable release quantity" in caplog.text
    assert "added together" in caplog.text
