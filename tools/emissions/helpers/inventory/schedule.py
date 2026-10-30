"""A plant's weekly and yearly schedule derived from its operating hours per year.

The Census QPC baseline gives plant hours per week, not days. The days per week are derived as
the hours per week over the configured working-day length, rounded up and at most 7; the hours
per day are the hours per week over those days. The weeks per year are the configured days per
year over 7, the same convention that turned hours per week into hours per year.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from config.plant_hours import PlantHoursSettings

DAYS_PER_WEEK_MAX = 7
HOURS_PER_YEAR_MAX = 8760.0
_ROUNDING_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Schedule:
    """How a plant runs.

    Attributes:
        days_per_week: Days a week the plant runs, d/week (derived, see module docstring).
        hours_per_day: Hours a day it runs, h/day.
        operating_days_per_year: Days a year it runs, d/yr.
        annual_operating_hours: Hours a year it runs, h/yr (at most 8,760).
    """

    days_per_week: int
    hours_per_day: float
    operating_days_per_year: float
    annual_operating_hours: float


def schedule_from_hours(hours_per_year: float, settings: PlantHoursSettings) -> Schedule:
    """The schedule of a plant that runs ``hours_per_year`` hours a year.

    Args:
        hours_per_year: Operating hours per year, h/yr; finite, > 0 and at most 8,760.
        settings: Supplies the working-day length and the days per year.

    Raises:
        ValueError: If the hours are not finite, not positive or above a year's hours.
    """
    if not math.isfinite(hours_per_year) or not 0 < hours_per_year <= HOURS_PER_YEAR_MAX:
        raise ValueError(f"hours_per_year must be in (0, 8760], got {hours_per_year!r}")
    weeks = settings.days_per_year / DAYS_PER_WEEK_MAX
    per_week = hours_per_year / weeks
    days = _days_per_week(per_week, settings.shift_hours_per_day)
    return Schedule(days, per_week / days, days * weeks, min(hours_per_year, HOURS_PER_YEAR_MAX))


def _days_per_week(hours_per_week: float, shift_hours: float) -> int:
    needed = math.ceil(hours_per_week / shift_hours - _ROUNDING_TOLERANCE)
    return max(1, min(DAYS_PER_WEEK_MAX, needed))
