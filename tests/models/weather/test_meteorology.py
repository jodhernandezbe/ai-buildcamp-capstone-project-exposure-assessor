"""Tests for models.weather.meteorology (synthetic hours, round numbers)."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from models.weather.meteorology import HourlyInputs, prevailing_direction, summarize_hours


def _hours(n: int = 4, **series: list[float] | list[bool]) -> HourlyInputs:
    base: dict[str, list[float] | list[bool]] = {
        "wind_speed": [4.0] * n,
        "wind_direction": [90.0] * n,
        "solar_radiation": [0.0] * n,
        "cloud_cover": [80.0] * n,
        "low_cloud_cover": [0.0] * n,
        "is_day": [False] * n,
        "temperature": [10.0] * n,
    }
    base.update(series)
    return HourlyInputs(
        wind_speed=np.asarray(base["wind_speed"], dtype=np.float64),
        wind_direction=np.asarray(base["wind_direction"], dtype=np.float64),
        solar_radiation=np.asarray(base["solar_radiation"], dtype=np.float64),
        cloud_cover=np.asarray(base["cloud_cover"], dtype=np.float64),
        low_cloud_cover=np.asarray(base["low_cloud_cover"], dtype=np.float64),
        is_day=np.asarray(base["is_day"], dtype=np.bool_),
        temperature=np.asarray(base["temperature"], dtype=np.float64),
    )


def _summary(hours: HourlyInputs, minimum: float = 1.0, width: float = 10.0):  # noqa: ANN202
    return summarize_hours(hours, minimum_wind_speed=minimum, sector_width=width)


def test_full_summary() -> None:
    summary = _summary(_hours(wind_speed=[2.0, 4.0, 6.0, 8.0], temperature=[0.0, 10.0, 20.0, 30.0]))
    assert summary.wind_speed == summary.mean_wind_speed == 5.0
    assert summary.wind_direction == 90.0
    assert summary.temperature == 15.0
    assert summary.hours == 4


def test_mean_wind_below_minimum_is_raised_to_it() -> None:
    summary = _summary(_hours(wind_speed=[0.2, 0.4, 0.6, 0.4]), minimum=1.0)
    assert summary.wind_speed == 1.0
    assert summary.mean_wind_speed == pytest.approx(0.4)


def test_modal_class_and_frequencies() -> None:
    # Cloudy night: 1.0 m/s -> F, 2.5 -> E, 4.0 -> D.
    summary = _summary(_hours(wind_speed=[1.0, 1.0, 1.0, 2.5, 4.0], n=5))
    assert summary.stability_class == "F"
    assert dict(summary.class_frequency) == {"D": 0.2, "E": 0.2, "F": 0.6}
    assert math.isclose(sum(summary.class_frequency.values()), 1.0)


def test_tied_classes_take_the_earliest_letter() -> None:
    summary = _summary(_hours(wind_speed=[1.0, 1.0, 4.0, 4.0]))
    assert summary.stability_class == "D"


def test_sector_wraps_around_north() -> None:
    assert prevailing_direction(np.asarray([358.0, 2.0, 4.0, 90.0]), 10.0) == 0.0
    assert prevailing_direction(np.asarray([355.0, 356.0, 3.0]), 10.0) == 0.0


def test_tied_sectors_take_the_smallest() -> None:
    assert prevailing_direction(np.asarray([90.0, 90.0, 270.0, 270.0]), 10.0) == 90.0


def test_sector_width_is_used() -> None:
    assert prevailing_direction(np.asarray([100.0, 110.0, 50.0]), 45.0) == 90.0


def test_missing_temperatures_are_left_out() -> None:
    summary = _summary(_hours(temperature=[10.0, math.nan, 20.0, math.nan]))
    assert summary.temperature == 15.0


def test_no_temperature_gives_nan() -> None:
    assert math.isnan(_summary(_hours(temperature=[math.nan] * 4)).temperature)


def test_frequencies_are_read_only() -> None:
    with pytest.raises(TypeError):
        _summary(_hours()).class_frequency["A"] = 1.0  # type: ignore[index]


def test_empty_series_raise() -> None:
    with pytest.raises(ValueError, match="empty"):
        _summary(_hours(n=0))


def test_mismatched_lengths_raise() -> None:
    hours = replace(_hours(), temperature=np.asarray([10.0], dtype=np.float64))
    with pytest.raises(ValueError, match="equal lengths"):
        _summary(hours)


def test_impossible_hour_raises() -> None:
    with pytest.raises(ValueError, match="cloud_cover"):
        _summary(_hours(cloud_cover=[80.0, 80.0, 150.0, 80.0]))


@pytest.mark.parametrize("width", [0.0, -10.0])
def test_invalid_sector_width_raises(width: float) -> None:
    with pytest.raises(ValueError, match="sector_width"):
        prevailing_direction(np.asarray([90.0]), width)
