"""Tests for the ``[meteorology]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.meteorology import (
    HOURLY_QUANTITIES,
    MeteorologySettings,
    load_meteorology_settings,
)

TEXT = """
[meteorology]
base_url = "https://met.test/"
archive_path = "/v1/a"
model = "m1"
wind_speed_unit = "ms"
timezone = "UTC"
coordinate_decimals = 3
delay_seconds = 0
timeout_seconds = 4
max_retries = 1
backoff_seconds = 0.5
default_year = 2000
first_year = 1990
archive_lag_days = 3
minimum_wind_speed = 0.5
sector_width = 20.0

[meteorology.variables]
temperature = "t"
wind_speed = "ws"
wind_direction = "wd"
solar_radiation = "sr"
cloud_cover = "cc"
low_cloud_cover = "lc"
is_day = "day"

[meteorology.units]
temperature = "°C"
wind_speed = "m/s"
wind_direction = "°"
solar_radiation = "W/m²"
cloud_cover = "%"
low_cloud_cover = "%"
is_day = ""

[meteorology.screening_default]
wind_speed = 2.0
wind_direction = 180.0
stability_class = "d"
ambient_temperature = 290.0
"""


def _load(tmp_path: Path, text: str = TEXT) -> MeteorologySettings:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_meteorology_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    settings = _load(tmp_path)
    request = settings.request
    assert request.url == "https://met.test/v1/a"
    assert (request.model, request.wind_speed_unit, request.timezone) == ("m1", "ms", "UTC")
    assert request.coordinate_decimals == 3
    assert request.variables["low_cloud_cover"] == "lc"
    assert request.units["solar_radiation"] == "W/m²"
    assert request.units["is_day"] == ""
    assert (settings.policy.delay_seconds, settings.policy.timeout_seconds) == (0, 4)
    assert (settings.policy.max_retries, settings.policy.backoff_seconds) == (1, 0.5)
    assert (settings.years.default_year, settings.years.first_year) == (2000, 1990)
    assert settings.years.archive_lag_days == 3
    assert (settings.summary.minimum_wind_speed, settings.summary.sector_width) == (0.5, 20.0)
    default = settings.screening_default
    assert (default.wind_speed, default.wind_direction) == (2.0, 180.0)
    assert (default.stability_class, default.ambient_temperature) == ("D", 290.0)


def test_default_file_loads() -> None:
    settings = load_meteorology_settings()
    assert settings.request.url.endswith("/v1/archive")
    assert settings.request.model == "era5"
    assert set(settings.request.variables) == set(HOURLY_QUANTITIES)
    assert settings.screening_default.ambient_temperature == 293.0
    assert settings.years.first_year <= settings.years.default_year


def test_tables_are_read_only(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        _load(tmp_path).request.units["wind_speed"] = "km/h"  # type: ignore[index]


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ('base_url = "https://met.test/"', 'base_url = ""', "meteorology.base_url"),
        ('archive_path = "/v1/a"', 'archive_path = "v1/a"', "meteorology.archive_path"),
        ('model = "m1"', "", "meteorology.model"),
        ('wind_speed_unit = "ms"', "wind_speed_unit = 1", "meteorology.wind_speed_unit"),
        ('timezone = "UTC"', "", "meteorology.timezone"),
        ("coordinate_decimals = 3", "coordinate_decimals = -1", "coordinate_decimals"),
        ("coordinate_decimals = 3", "coordinate_decimals = 7", "coordinate_decimals"),
        ("delay_seconds = 0", "delay_seconds = -1", "meteorology.delay_seconds"),
        ("timeout_seconds = 4", "timeout_seconds = 0", "meteorology.timeout_seconds"),
        ("timeout_seconds = 4", "timeout_seconds = true", "meteorology.timeout_seconds"),
        ("max_retries = 1", "max_retries = 1.5", "meteorology.max_retries"),
        ("backoff_seconds = 0.5", 'backoff_seconds = "x"', "meteorology.backoff_seconds"),
        ("default_year = 2000", "default_year = 1980", "first_year must not be later"),
        ("first_year = 1990", "first_year = 0", "meteorology.first_year"),
        ("archive_lag_days = 3", "archive_lag_days = -1", "meteorology.archive_lag_days"),
        ("minimum_wind_speed = 0.5", "minimum_wind_speed = 0", "minimum_wind_speed"),
        ("sector_width = 20.0", "sector_width = 7.0", "divide 360"),
        ("sector_width = 20.0", "sector_width = 720.0", "divide 360"),
        ("sector_width = 20.0", "sector_width = -10.0", "meteorology.sector_width"),
        ('temperature = "t"', "", "meteorology.variables.temperature"),
        ('is_day = "day"', 'is_day = ""', "meteorology.variables.is_day"),
        ('low_cloud_cover = "lc"', 'low_clouds = "lc"', "unknown quantities: low_clouds"),
        ('wind_direction = "°"', "wind_direction = 1", "meteorology.units.wind_direction"),
        ('stability_class = "d"', 'stability_class = "G"', "stability_class"),
        ("wind_direction = 180.0", "wind_direction = 360.0", "wind_direction must be below 360"),
        ("wind_direction = 180.0", "wind_direction = -5.0", "screening_default.wind_direction"),
        ("wind_speed = 2.0", "wind_speed = 0.0", "screening_default.wind_speed"),
        ("ambient_temperature = 290.0", "", "screening_default.ambient_temperature"),
    ],
)
def test_invalid_entries_name_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    assert old in TEXT
    with pytest.raises(ValueError, match=key):
        _load(tmp_path, TEXT.replace(old, new, 1))


@pytest.mark.parametrize("table", ["[meteorology.variables]", "[meteorology.units]"])
def test_missing_subtable(tmp_path: Path, table: str) -> None:
    head, tail = TEXT.split(table)
    rest = tail.split("\n[", 1)[1]
    with pytest.raises(ValueError, match=table.strip("[]")):
        _load(tmp_path, head + "[" + rest)


def test_section_and_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="meteorology section"):
        _load(tmp_path, "[other]\nx = 1\n")
    with pytest.raises(FileNotFoundError):
        load_meteorology_settings(tmp_path / "absent.toml")
