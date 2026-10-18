"""Tests for models.transport.wind_profile (EPA-454/R-92-019 equation 3.1, Table 3-1)."""

from __future__ import annotations

import math

import pytest

from models.transport.wind_profile import wind_speed_at_height


def test_power_law_hand_computed() -> None:
    # 4 * (100 / 10)^0.15 = 4 * 10^0.15
    assert wind_speed_at_height(4.0, 100.0, 0.15) == pytest.approx(4.0 * 10**0.15)
    assert wind_speed_at_height(4.0, 100.0, 0.15) == pytest.approx(5.650, abs=0.001)


def test_no_adjustment_below_ten_meters() -> None:
    assert wind_speed_at_height(4.0, 9.99, 0.55) == 4.0
    assert wind_speed_at_height(4.0, 0.0, 0.55) == 4.0


def test_reference_height_is_unchanged() -> None:
    assert wind_speed_at_height(4.0, 10.0, 0.55) == 4.0


def test_taller_release_has_more_wind_and_more_so_when_stable() -> None:
    unstable = wind_speed_at_height(4.0, 100.0, 0.07)
    stable = wind_speed_at_height(4.0, 100.0, 0.55)
    assert 4.0 < unstable < stable


def test_zero_exponent_means_no_change() -> None:
    assert wind_speed_at_height(4.0, 200.0, 0.0) == 4.0


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 50.0, 0.1),
        (-1.0, 50.0, 0.1),
        (math.nan, 50.0, 0.1),
        (4.0, -1.0, 0.1),
        (4.0, 50.0, -0.1),
        (4.0, math.inf, 0.1),
        (True, 50.0, 0.1),
    ],
)
def test_rejects_impossible_input(args: tuple[float, float, float]) -> None:
    with pytest.raises(ValueError):
        wind_speed_at_height(*args)
