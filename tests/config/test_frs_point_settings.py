"""Tests for the ``[frs_point]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.frs_point import load_frs_point_settings

TEXT = """
[frs_point]
path = "/p/{frs_id}/JSON"
latitude_field = " la "
longitude_field = "lo"
timestamp_field = "ts"
"""


def test_explicit_values(tmp_path: Path) -> None:
    settings = load_frs_point_settings(_write(tmp_path))
    assert (settings.path, settings.latitude_field) == ("/p/{frs_id}/JSON", "la")
    assert (settings.longitude_field, settings.timestamp_field) == ("lo", "ts")


def _write(tmp_path: Path, text: str = TEXT) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


def test_default_file_loads() -> None:
    settings = load_frs_point_settings()
    assert "{frs_id}" in settings.path
    assert settings.latitude_field == "latitude83"


def test_path_needs_the_placeholder(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="frs_point.path"):
        load_frs_point_settings(_write(tmp_path, TEXT.replace("{frs_id}", "x")))


@pytest.mark.parametrize("key", ["path", "latitude_field", "longitude_field", "timestamp_field"])
def test_each_key_is_required(tmp_path: Path, key: str) -> None:
    text = "\n".join(line for line in TEXT.splitlines() if not line.startswith(key))
    with pytest.raises(ValueError, match=key):
        load_frs_point_settings(_write(tmp_path, text))


def test_section_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="frs_point"):
        load_frs_point_settings(_write(tmp_path, "[x]\na = 1\n"))
