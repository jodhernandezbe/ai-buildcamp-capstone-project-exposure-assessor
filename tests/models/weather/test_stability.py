"""Tests for models.weather.stability against EPA-454/R-99-005 Tables 6-7 (SRDT) and 6-4."""

from __future__ import annotations

import math

import pytest

from models.weather.stability import classify_stability

# SRDT daytime key, written out from Table 6-7: one representative speed per wind band, one
# representative radiation per column (>=925, 675-925, 175-675, <175 W/m^2).
DAY_SPEEDS = (1.0, 2.5, 4.0, 5.5, 8.0)
DAY_RADIATION = (950.0, 800.0, 400.0, 100.0)
DAY_TABLE = ("AABD", "ABCD", "BBCD", "CCDD", "CDDD")


@pytest.mark.parametrize("row", range(5))
@pytest.mark.parametrize("column", range(4))
def test_daytime_matches_table_6_7(row: int, column: int) -> None:
    cls = classify_stability(DAY_SPEEDS[row], DAY_RADIATION[column], 0.0, 0.0, True)
    assert cls == DAY_TABLE[row][column]


@pytest.mark.parametrize(
    ("speed", "radiation", "expected"),
    [
        (1.99, 925.0, "A"),  # radiation bound inclusive, speed bound exclusive
        (2.0, 925.0, "A"),
        (2.0, 924.9, "B"),
        (3.0, 675.0, "B"),
        (2.99, 674.9, "C"),
        (5.0, 175.0, "D"),
        (4.99, 175.0, "C"),
        (6.0, 925.0, "C"),
        (0.0, 0.0, "D"),
    ],
)
def test_daytime_band_edges(speed: float, radiation: float, expected: str) -> None:
    assert classify_stability(speed, radiation, 0.0, 0.0, True) == expected


# Turner's key, Table 6-4 (classes 6 and 7 as F): index -1 (cloud > 4/10) and -2 (<= 4/10).
@pytest.mark.parametrize(
    ("speed", "cloudy", "clear"),
    [
        (0.0, "F", "F"),
        (0.5, "F", "F"),  # 0 - 0.7 m/s
        (1.5, "F", "F"),  # 0.8 - 1.8
        (2.5, "E", "F"),  # 1.9 - 2.8
        (3.0, "E", "F"),  # 2.9 - 3.3
        (3.5, "D", "E"),  # 3.4 - 3.8
        (4.5, "D", "E"),  # 3.9 - 4.8
        (5.0, "D", "E"),  # 4.9 - 5.4
        (5.7, "D", "D"),  # 5.5 - 5.9
        (9.0, "D", "D"),  # 6.0 and above
    ],
)
def test_night_matches_turner(speed: float, cloudy: str, clear: str) -> None:
    assert classify_stability(speed, 0.0, 80.0, 0.0, False) == cloudy
    assert classify_stability(speed, 0.0, 20.0, 0.0, False) == clear


@pytest.mark.parametrize(
    ("speed", "cloud", "expected"),
    [(1.89, 41.0, "F"), (1.9, 41.0, "E"), (3.39, 41.0, "E"), (3.4, 41.0, "D")]
    + [(3.39, 40.0, "F"), (3.4, 40.0, "E"), (5.49, 40.0, "E"), (5.5, 40.0, "D")],
)
def test_night_band_edges(speed: float, cloud: float, expected: str) -> None:
    assert classify_stability(speed, 0.0, cloud, 0.0, False) == expected


def test_night_ignores_radiation() -> None:
    assert classify_stability(1.0, 500.0, 0.0, 0.0, False) == "F"


@pytest.mark.parametrize("is_day", [True, False])
@pytest.mark.parametrize("speed", [0.5, 2.5, 4.0, 8.0])
def test_low_overcast_is_neutral_day_or_night(is_day: bool, speed: float) -> None:
    assert classify_stability(speed, 950.0, 100.0, 100.0, is_day) == "D"


def test_almost_low_overcast_is_not_neutral() -> None:
    assert classify_stability(0.5, 0.0, 100.0, 99.9, False) == "F"


@pytest.mark.parametrize(
    ("args", "name"),
    [
        ((-1.0, 0.0, 0.0, 0.0), "wind_speed"),
        ((math.nan, 0.0, 0.0, 0.0), "wind_speed"),
        ((math.inf, 0.0, 0.0, 0.0), "wind_speed"),
        ((1.0, -5.0, 0.0, 0.0), "solar_radiation"),
        ((1.0, 0.0, 120.0, 0.0), "cloud_cover"),
        ((1.0, 0.0, -1.0, 0.0), "cloud_cover"),
        ((1.0, 0.0, 0.0, 101.0), "low_cloud_cover"),
        ((1.0, 0.0, 0.0, math.nan), "low_cloud_cover"),
        ((True, 0.0, 0.0, 0.0), "wind_speed"),
    ],
)
def test_impossible_hours_raise(args: tuple[float, float, float, float], name: str) -> None:
    with pytest.raises(ValueError, match=name):
        classify_stability(*args, True)
