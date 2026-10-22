"""Tests for the ``[plant_hours]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.plant_hours import (
    PlantHoursSettings,
    get_plant_hours_settings,
    load_plant_hours_settings,
)

GOOD = {
    "baseline_path": '"data/x.parquet"',
    "code_column": '"code"',
    "hours_column": '"hours"',
    "min_digits": "3",
    "max_digits": "6",
    "days_per_year": "365",
    "max_hours_per_week": "168",
}


def _load(tmp_path: Path, **override: str) -> PlantHoursSettings:
    values = {**GOOD, **override}
    body = "\n".join(f"{key} = {value}" for key, value in values.items())
    path = tmp_path / "settings.toml"
    path.write_text(f"[plant_hours]\n{body}\n", encoding="utf-8")
    return load_plant_hours_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert (s.code_column, s.hours_column, s.min_digits, s.max_digits) == ("code", "hours", 3, 6)
    assert (s.days_per_year, s.max_hours_per_week) == (365.0, 168.0)
    assert s.baseline_path.is_absolute() and s.baseline_path.name == "x.parquet"


def test_shipped_settings_point_at_the_committed_baseline() -> None:
    s = get_plant_hours_settings()
    assert s.baseline_path.is_file()
    assert (s.min_digits, s.max_digits, s.days_per_year) == (3, 6, 365.0)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("min_digits", "0"),
        ("min_digits", "true"),
        ("min_digits", "7"),
        ("max_digits", "2"),
        ("days_per_year", "0"),
        ("days_per_year", "nan"),
        ("days_per_year", "true"),
        ("max_hours_per_week", "0"),
        ("code_column", '""'),
        ("hours_column", "5"),
        ("baseline_path", '""'),
    ],
)
def test_invalid_values_name_the_key(tmp_path: Path, key: str, value: str) -> None:
    with pytest.raises(ValueError, match=key):
        _load(tmp_path, **{key: value})


def test_missing_section(tmp_path: Path) -> None:
    path = tmp_path / "s.toml"
    path.write_text("[other]\na = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="plant_hours"):
        load_plant_hours_settings(path)
