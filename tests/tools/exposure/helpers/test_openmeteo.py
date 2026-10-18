"""Tests for tools.exposure.helpers.openmeteo (no network: an httpx mock transport)."""

from __future__ import annotations

import math
from copy import deepcopy

import httpx
import numpy as np
import pytest

from config.meteorology import HOURLY_QUANTITIES, load_meteorology_settings
from tools.exposure.helpers.openmeteo import ArchiveError, archive_params, fetch_hourly
from tools.http import RetryingClient

SETTINGS = load_meteorology_settings()
REQUEST = SETTINGS.request
NAMES = REQUEST.variables
GOOD_ROW = {
    "temperature": 10.0,
    "wind_speed": 4.0,
    "wind_direction": 90.0,
    "solar_radiation": 0.0,
    "cloud_cover": 50.0,
    "low_cloud_cover": 0.0,
    "is_day": 0,
}


class _Policy:
    delay_seconds = 0.0
    timeout_seconds = 5.0
    max_retries = 0
    backoff_seconds = 0.0


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "latitude": 41.5,
        "hourly": {NAMES[q]: [row[q] for row in rows] for q in HOURLY_QUANTITIES},
        "hourly_units": {NAMES[q]: REQUEST.units[q] for q in HOURLY_QUANTITIES},
    }


def _row(**changes: object) -> dict[str, object]:
    return {**GOOD_ROW, **changes}


def _fetch(payload: object, status: int = 200) -> tuple[object, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=payload)

    client = RetryingClient(_Policy(), httpx.Client(transport=httpx.MockTransport(handler)))
    return fetch_hourly(41.5, -71.25, 2000, REQUEST, client), seen


def test_request_parameters_come_from_the_settings() -> None:
    params = archive_params(41.123456, -71.987654, 2000, REQUEST)
    assert params["latitude"] == round(41.123456, REQUEST.coordinate_decimals)
    assert params["longitude"] == round(-71.987654, REQUEST.coordinate_decimals)
    assert (params["start_date"], params["end_date"]) == ("2000-01-01", "2000-12-31")
    assert params["models"] == REQUEST.model
    assert params["wind_speed_unit"] == REQUEST.wind_speed_unit
    assert params["timezone"] == REQUEST.timezone
    assert set(str(params["hourly"]).split(",")) == set(NAMES.values())


def test_valid_hours_are_returned_and_the_request_goes_to_the_configured_url() -> None:
    data, seen = _fetch(_payload([_row(), _row(wind_speed=6.0, is_day=1)]))
    assert (data.total, data.excluded) == (2, 0)  # type: ignore[attr-defined]
    assert list(data.hours.wind_speed) == [4.0, 6.0]  # type: ignore[attr-defined]
    assert list(data.hours.is_day) == [False, True]  # type: ignore[attr-defined]
    assert str(seen[0].url).startswith(REQUEST.url)


@pytest.mark.parametrize(
    "bad",
    [
        {"wind_speed": None},
        {"wind_speed": -1.0},
        {"wind_speed": "fast"},
        {"wind_speed": True},
        {"wind_direction": None},
        {"wind_direction": 361.0},
        {"wind_direction": -1.0},
        {"solar_radiation": None},
        {"solar_radiation": -5.0},
        {"cloud_cover": None},
        {"cloud_cover": 101.0},
        {"low_cloud_cover": None},
        {"low_cloud_cover": -1.0},
        {"is_day": None},
        {"is_day": 2},
    ],
)
def test_an_hour_with_a_bad_required_value_is_excluded(bad: dict[str, object]) -> None:
    data, _ = _fetch(_payload([_row(), _row(**bad), _row()]))
    assert (data.total, data.excluded) == (3, 1)  # type: ignore[attr-defined]


def test_a_missing_temperature_does_not_exclude_the_hour() -> None:
    data, _ = _fetch(_payload([_row(temperature=None), _row(temperature=20.0)]))
    assert data.excluded == 0  # type: ignore[attr-defined]
    temperatures = [float(v) for v in data.hours.temperature]  # type: ignore[attr-defined]
    assert math.isnan(temperatures[0])
    assert temperatures[1] == 20.0


def test_direction_of_exactly_360_is_kept() -> None:
    data, _ = _fetch(_payload([_row(wind_direction=360.0)]))
    assert data.excluded == 0  # type: ignore[attr-defined]


def test_every_hour_bad_leaves_no_hours() -> None:
    data, _ = _fetch(_payload([_row(wind_speed=None), _row(wind_speed=-1.0)]))
    assert (data.total, data.excluded) == (2, 2)  # type: ignore[attr-defined]
    assert len(data.hours.wind_speed) == 0  # type: ignore[attr-defined]
    assert isinstance(data.hours.wind_speed, np.ndarray)  # type: ignore[attr-defined]


def test_an_empty_series_is_zero_hours() -> None:
    data, _ = _fetch(_payload([]))
    assert (data.total, data.excluded) == (0, 0)  # type: ignore[attr-defined]


@pytest.mark.parametrize("payload", [[], "text", 5, None, {"hourly": []}, {"hourly_units": {}}])
def test_unexpected_shape_is_an_archive_error(payload: object) -> None:
    with pytest.raises(ArchiveError):
        _fetch(payload)


def test_a_missing_series_is_named() -> None:
    payload = _payload([_row()])
    del payload["hourly"][NAMES["low_cloud_cover"]]  # type: ignore[attr-defined]
    with pytest.raises(ArchiveError, match=NAMES["low_cloud_cover"]):
        _fetch(payload)


def test_a_non_list_series_is_an_archive_error() -> None:
    payload = _payload([_row()])
    payload["hourly"][NAMES["wind_speed"]] = "oops"  # type: ignore[index]
    with pytest.raises(ArchiveError, match=NAMES["wind_speed"]):
        _fetch(payload)


def test_series_of_different_lengths_are_an_archive_error() -> None:
    payload = _payload([_row(), _row()])
    payload["hourly"][NAMES["temperature"]].pop()  # type: ignore[attr-defined]
    with pytest.raises(ArchiveError, match="different lengths"):
        _fetch(payload)


@pytest.mark.parametrize("quantity", ["wind_speed", "temperature", "wind_direction"])
def test_a_unit_that_is_not_the_one_asked_for_is_an_archive_error(quantity: str) -> None:
    payload = deepcopy(_payload([_row()]))
    payload["hourly_units"][NAMES[quantity]] = "km/h"  # type: ignore[index]
    with pytest.raises(ArchiveError, match="expected"):
        _fetch(payload)


@pytest.mark.parametrize("status", [400, 404, 500])
def test_http_failures_are_archive_errors(status: int) -> None:
    with pytest.raises(ArchiveError, match="could not be read"):
        _fetch({"reason": "x"}, status=status)
