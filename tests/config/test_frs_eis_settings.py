"""Tests for the ``[frs_eis]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.frs_eis import load_frs_eis_settings

TEXT = """
[frs_eis]
base_url = " https://frs.test/svc "
eis_path = "/e/{frs_ids}/EIS"
registry_field = "id"
eis_id_field = "eis"
sites_path = "/s/{frs_ids}"
twins_path = "/t/{name}/{state}"
name_field = "name"
state_field = "st"
latitude_field = "lat"
longitude_field = "lon"
batch_size = 25
max_twin_distance_km = 0.25
twin_workers = 3
cache_seconds = 60
"""


def _load(tmp_path: Path, text: str = TEXT):  # noqa: ANN202  # the dataclass type is the point
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_frs_eis_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert (s.base_url, s.eis_path, s.sites_path, s.twins_path) == (
        "https://frs.test/svc",
        "/e/{frs_ids}/EIS",
        "/s/{frs_ids}",
        "/t/{name}/{state}",
    )
    assert (s.registry_field, s.eis_id_field, s.name_field, s.state_field) == (
        "id",
        "eis",
        "name",
        "st",
    )
    assert (s.latitude_field, s.longitude_field) == ("lat", "lon")
    assert (s.batch_size, s.max_twin_distance_km) == (25, 0.25)
    assert (s.twin_workers, s.cache_seconds) == (3, 60.0)


def test_default_file_loads() -> None:
    s = load_frs_eis_settings()
    assert s.base_url.startswith("https://")
    assert "{frs_ids}" in s.eis_path and "{frs_ids}" in s.sites_path
    assert "{name}" in s.twins_path and "{state}" in s.twins_path
    assert 1 <= s.batch_size < 200  # 200 IDs were answered, 400 refused, by this service
    assert 0 < s.max_twin_distance_km <= 1.0


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ('"/e/{frs_ids}/EIS"', '"/e/x/EIS"', "eis_path"),
        ('"/e/{frs_ids}/EIS"', '"e/{frs_ids}"', "eis_path"),
        ('"/s/{frs_ids}"', '"/s/x"', "sites_path"),
        ('"/t/{name}/{state}"', '"/t/{name}"', "twins_path"),
        ('registry_field = "id"', "", "registry_field"),
        ('eis_id_field = "eis"', 'eis_id_field = " "', "eis_id_field"),
        ('name_field = "name"', "", "name_field"),
        ('state_field = "st"', "", "state_field"),
        ('latitude_field = "lat"', "", "latitude_field"),
        ('longitude_field = "lon"', "", "longitude_field"),
        ("batch_size = 25", "batch_size = 0", "batch_size"),
        ("batch_size = 25", "batch_size = true", "batch_size"),
        ("max_twin_distance_km = 0.25", "max_twin_distance_km = 0", "max_twin_distance_km"),
        ("max_twin_distance_km = 0.25", 'max_twin_distance_km = "near"', "max_twin_distance_km"),
        ("twin_workers = 3", "twin_workers = 0", "twin_workers"),
        ("twin_workers = 3", "twin_workers = true", "twin_workers"),
        ("cache_seconds = 60", "cache_seconds = -1", "cache_seconds"),
        ("cache_seconds = 60", "", "cache_seconds"),
    ],
)
def test_invalid_entries_name_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    assert old in TEXT
    with pytest.raises(ValueError, match=key):
        _load(tmp_path, TEXT.replace(old, new, 1))


def test_section_and_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="frs_eis section"):
        _load(tmp_path, "[other]\nx = 1\n")
    with pytest.raises(FileNotFoundError):
        load_frs_eis_settings(tmp_path / "absent.toml")
