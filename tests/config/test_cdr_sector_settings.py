"""Tests for the ``[cdr_sector]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.cdr_sector import get_cdr_sector_settings, load_cdr_sector_settings

TEXT = """
[cdr_sector]
crosswalk_path = "data/x.csv"
prefix_column = "p"
code_column = "c"
title_column = "t"
edition_column = "e"
min_digits = 2
max_digits = 6
"""


def test_explicit_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(TEXT, encoding="utf-8")
    s = load_cdr_sector_settings(path)
    assert (s.prefix_column, s.code_column, s.min_digits, s.max_digits) == ("p", "c", 2, 6)
    assert s.crosswalk_path.is_absolute()


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ("min_digits = 2", "min_digits = 0", "min_digits"),
        ("min_digits = 2", "min_digits = 7", "min_digits"),
        ("min_digits = 2", "min_digits = true", "min_digits"),
        ('code_column = "c"', 'code_column = ""', "code_column"),
        ('crosswalk_path = "data/x.csv"\n', "", "crosswalk_path"),
    ],
)
def test_invalid_values_name_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(TEXT.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ValueError, match=key):
        load_cdr_sector_settings(path)


def test_shipped_settings_point_at_the_committed_file() -> None:
    assert get_cdr_sector_settings().crosswalk_path.is_file()
