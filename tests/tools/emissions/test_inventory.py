"""Tests for query_emissions_inventory."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from config.efservice import get_efservice_settings
from tools.emissions import inventory
from tools.emissions.inventory import query_emissions_inventory
from tools.registry import get_all_tools

CURRENT_YEAR = 2012  # the fixture rows are real and run from 1988 to 2009
ROWS = json.loads((Path(__file__).parent / "helpers" / "inventory" / "tri_rows.json").read_text())


@pytest.fixture
def requests_seen(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "GEO_FACILITY_POINT" in str(request.url):
            return httpx.Response(200, json=[])  # FRS has no point either
        seen.append(request)
        return httpx.Response(200, json=ROWS)

    monkeypatch.setattr(
        inventory, "_open_client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )
    settings = replace(get_efservice_settings(), delay_seconds=0.0, backoff_seconds=0.0)
    monkeypatch.setattr(inventory, "get_efservice_settings", lambda: settings)
    monkeypatch.setattr(inventory, "_current_year", lambda: CURRENT_YEAR)
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
    url = str(requests_seen[0].url)
    assert "/cas_registry_number/50-00-0/environmental_medium/AIR%20STACK/" in url
    assert "/reporting_year/%3E/2002/rows/0:" in url  # the last ten years ending in 2012
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


def test_a_facility_that_stopped_reporting_long_ago_is_not_returned(
    requests_seen: list[httpx.Request], monkeypatch: pytest.MonkeyPatch
) -> None:
    """In 2026 only 2017 and later count; the fixture's last report is 2009."""
    monkeypatch.setattr(inventory, "_current_year", lambda: 2026)
    assert query_emissions_inventory.invoke({"cas_number": "50-00-0"}) == []


def test_every_record_carries_its_submission_control_number(
    requests_seen: list[httpx.Request],
) -> None:
    records = query_emissions_inventory.invoke({"cas_number": "50-00-0"})
    assert records and all("doc_ctrl_num" in record for record in records)
    assert any(record["doc_ctrl_num"] for record in records)


def test_description_explains_the_window_and_the_control_number() -> None:
    text = " ".join(query_emissions_inventory.description.split())
    for phrase in ("last 10 reporting years", "doc_ctrl_num", "fetch_facility_industry"):
        assert phrase in text, phrase
