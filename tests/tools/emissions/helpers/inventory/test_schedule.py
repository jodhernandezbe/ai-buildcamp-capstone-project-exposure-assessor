"""Tests for the schedule derived from operating hours per year."""

from __future__ import annotations

import pytest

from config.plant_hours import get_plant_hours_settings
from tools.emissions.helpers.inventory.schedule import schedule_from_hours

SETTINGS = get_plant_hours_settings()
WEEKS = SETTINGS.days_per_year / 7


def test_single_shift_plant_runs_five_days() -> None:
    schedule = schedule_from_hours(40 * WEEKS, SETTINGS)
    assert schedule.days_per_week == 5
    assert schedule.hours_per_day == pytest.approx(8.0)
    assert schedule.operating_days_per_year == pytest.approx(5 * WEEKS)
    assert schedule.annual_operating_hours == pytest.approx(40 * WEEKS)


def test_two_shift_plant_is_capped_at_seven_days() -> None:
    schedule = schedule_from_hours(80 * WEEKS, SETTINGS)
    assert schedule.days_per_week == 7
    assert schedule.hours_per_day == pytest.approx(80 / 7)


def test_continuous_plant_runs_all_hours() -> None:
    schedule = schedule_from_hours(8760.0, SETTINGS)
    assert (schedule.days_per_week, schedule.hours_per_day) == (7, pytest.approx(24.0))
    assert schedule.operating_days_per_year == pytest.approx(365.0)
    assert schedule.annual_operating_hours == 8760.0


def test_days_times_hours_give_the_annual_hours() -> None:
    for hours in (500.0, 2087.0, 4380.0, 8000.0):
        s = schedule_from_hours(hours, SETTINGS)
        assert s.operating_days_per_year * s.hours_per_day == pytest.approx(hours)


def test_very_short_week_is_one_day() -> None:
    assert schedule_from_hours(4 * WEEKS, SETTINGS).days_per_week == 1


@pytest.mark.parametrize("hours", [0.0, -1.0, 9000.0, float("nan"), float("inf")])
def test_impossible_hours_raise(hours: float) -> None:
    with pytest.raises(ValueError):
        schedule_from_hours(hours, SETTINGS)
