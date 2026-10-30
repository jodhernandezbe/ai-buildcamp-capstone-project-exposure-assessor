"""Typed loader for the ``[plant_hours]`` settings (operating hours by NAICS code)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import (
    project_path,
    read_toml,
    require_int,
    require_number,
    require_str,
    section,
)

NAME = "plant_hours"
_HOURS_PER_DAY = 24.0


@dataclass(frozen=True)
class PlantHoursSettings:
    """Where the plant-hours baseline is and how a NAICS code is matched against it.

    Attributes:
        baseline_path: Parquet of average plant hours per week by NAICS code; absolute or
            resolved against the project root.
        code_column: Column holding the NAICS code (a digit string).
        hours_column: Column holding the average plant hours per week, in h/week.
        min_digits: Shortest code prefix tried when matching a facility's code.
        max_digits: Longest code accepted, in the baseline and for a facility.
        days_per_year: Days in a year, d/yr; hours per year = h/week x days_per_year / 7.
        max_hours_per_week: Largest plausible hours per week (24 h x 7 d = 168), in h/week.
        shift_hours_per_day: Hours of one working day, used to derive how many days a week a
            plant with the matched hours per week runs (QPC gives hours, not days), in h/day.
    """

    baseline_path: Path
    code_column: str
    hours_column: str
    min_digits: int
    max_digits: int
    days_per_year: float
    max_hours_per_week: float
    shift_hours_per_day: float


def _text(table: dict[str, object], key: str) -> str:
    return require_str(table, key, NAME).strip()


def _digits(table: dict[str, object]) -> tuple[int, int]:
    low = require_int(table, "min_digits", minimum=1, name=NAME)
    high = require_int(table, "max_digits", minimum=1, name=NAME)
    if low > high:
        raise ValueError(f"{NAME}.min_digits must be at most {NAME}.max_digits")
    return low, high


def _shift_hours(table: dict[str, object]) -> float:
    hours = require_number(table, "shift_hours_per_day", minimum=1e-9, name=NAME)
    if hours > _HOURS_PER_DAY:
        raise ValueError(f"{NAME}.shift_hours_per_day must be at most 24")
    return hours


def load_plant_hours_settings(path: Path | None = None) -> PlantHoursSettings:
    """Load and validate the plant-hours settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), NAME)
    low, high = _digits(table)
    return PlantHoursSettings(
        baseline_path=project_path(table, "baseline_path", NAME),
        code_column=_text(table, "code_column"),
        hours_column=_text(table, "hours_column"),
        min_digits=low,
        max_digits=high,
        days_per_year=require_number(table, "days_per_year", minimum=1, name=NAME),
        max_hours_per_week=require_number(table, "max_hours_per_week", minimum=1, name=NAME),
        shift_hours_per_day=_shift_hours(table),
    )


@lru_cache(maxsize=1)
def get_plant_hours_settings() -> PlantHoursSettings:
    """Return the cached plant-hours settings from the default file."""
    return load_plant_hours_settings()
