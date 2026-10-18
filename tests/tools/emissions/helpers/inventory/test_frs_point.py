"""Tests for tools.emissions.helpers.inventory.frs_point."""

from __future__ import annotations

import logging

import httpx
import pytest

from config.efservice import EfserviceSettings
from config.frs_point import FrsPointSettings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.frs_point import FrsLocator
from tools.emissions.helpers.inventory.reduce import Location

SETTINGS = FrsPointSettings("/p/{frs_id}/JSON", "lat", "lon", "ts")
EF = EfserviceSettings("https://ef.test/api", 0.0, 5.0, 0, 0.0)


def _locator(payload: object, status: int = 200) -> tuple[FrsLocator, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=payload)

    client = EfserviceClient(
        EF, httpx.Client(transport=httpx.MockTransport(handler)), lambda _: None
    )
    return FrsLocator(client, SETTINGS), seen


def test_a_point_is_returned() -> None:
    locator, seen = _locator([{"lat": 10.5, "lon": -20.25, "ts": "2020"}])
    assert locator("110000000001") == Location(10.5, -20.25)
    assert str(seen[0].url).endswith("/p/110000000001/JSON")


def test_the_newest_valid_point_wins() -> None:
    rows = [
        {"lat": 1.0, "lon": -1.0, "ts": "2019-01-01"},
        {"lat": 2.0, "lon": -2.0, "ts": "2024-01-01"},
        {"lat": None, "lon": None, "ts": "2025-01-01"},
    ]
    assert _locator(rows)[0]("110000000001") == Location(2.0, -2.0)


def test_answers_are_remembered() -> None:
    locator, seen = _locator([{"lat": 1.0, "lon": -1.0, "ts": "x"}])
    locator("110000000001")
    locator("110000000001")
    assert len(seen) == 1


@pytest.mark.parametrize(
    "row",
    [
        {"lat": 91.0, "lon": -1.0},
        {"lat": 1.0, "lon": 181.0},
        {"lat": True, "lon": -1.0},
        {"lat": "1", "lon": "-1"},
        {"lat": 1.0},
    ],
)
def test_unusable_points_give_none(row: dict[str, object]) -> None:
    assert _locator([row])[0]("110000000001") is None


def test_no_point_gives_none() -> None:
    assert _locator([])[0]("110000000001") is None


@pytest.mark.parametrize("bad", ["", "abc", "11-00"])
def test_an_invalid_id_makes_no_request(bad: str) -> None:
    locator, seen = _locator([])
    assert locator(bad) is None
    assert seen == []


def test_a_failed_request_gives_none_and_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    locator, _ = _locator({"error": "x"}, status=500)
    with caplog.at_level(logging.WARNING):
        assert locator("110000000001") is None
    assert "could not be read" in caplog.text
