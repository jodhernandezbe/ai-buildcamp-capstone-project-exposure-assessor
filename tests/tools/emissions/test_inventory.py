"""Tests for query_emissions_inventory."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from config.loader import load_tri_settings
from tools.emissions import inventory
from tools.emissions.inventory import query_emissions_inventory
from tools.registry import get_all_tools

ROWS = json.loads((Path(__file__).parent / "helpers" / "tri_rows.json").read_text())


@pytest.fixture
def requests_seen(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=ROWS)

    monkeypatch.setattr(
        inventory, "_open_client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )
    settings = replace(load_tri_settings(), delay_seconds=0.0, backoff_seconds=0.0)
    monkeypatch.setattr(inventory, "get_tri_settings", lambda: settings)
    return seen


def test_schema() -> None:
    assert query_emissions_inventory.name == "query_emissions_inventory"
    assert set(query_emissions_inventory.args) == {"cas_number"}
    assert query_emissions_inventory.description
    assert query_emissions_inventory in get_all_tools()


def test_docstring_describes_every_returned_field() -> None:
    text = query_emissions_inventory.description
    for field in (
        "frs_id",
        "emission_rate",
        "total_release",
        "unit",
        "operating_hours_per_year",
        "latitude",
    ):
        assert field in text
    assert "reporting_year" in text


def test_returns_latest_records_with_rates(requests_seen: list[httpx.Request]) -> None:
    records = query_emissions_inventory.invoke({"cas_number": "50-00-0"})
    assert len(requests_seen) == 1
    assert "/cas_registry_number/50-00-0/environmental_medium/AIR%20STACK/rows/0:" in str(
        requests_seen[0].url
    )
    by_id = {r["frs_id"]: r for r in records}
    assert by_id["110000307864"]["reporting_year"] == 2009
    assert by_id["110000307864"]["unit"] == "Pounds"
    assert by_id["110000307864"]["emission_rate"] == pytest.approx(
        31070 * 453.59237 / (8760 * 3600)
    )
    assert by_id["110000307864"]["operating_hours_per_year"] == 8760.0


def test_bare_cas_is_accepted(requests_seen: list[httpx.Request]) -> None:
    query_emissions_inventory.invoke({"cas_number": " 50000 "})
    assert "/cas_registry_number/50-00-0/" in str(requests_seen[0].url)


@pytest.mark.parametrize("bad", ["", "abc", "50-00-1", "1-2-3", "50-00-0; DROP"])
def test_invalid_cas_makes_no_request(
    requests_seen: list[httpx.Request], caplog: pytest.LogCaptureFixture, bad: str
) -> None:
    with caplog.at_level(logging.WARNING):
        assert query_emissions_inventory.invoke({"cas_number": bad}) == []
    assert requests_seen == []
    assert "not a valid CAS" in caplog.text
