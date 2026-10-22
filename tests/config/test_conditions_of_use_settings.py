"""Tests for the ``[conditions_of_use]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.conditions_of_use import (
    ConditionsSettings,
    get_conditions_settings,
    load_conditions_settings,
)
from config.loader import get_tri_settings

BASE = """
[conditions_of_use]
crosswalk_path = "data/x.csv"
level = "L1"
level_column = "lvl"
section_column = "sec"
subuse_column = "sub"
stage_column = "stage"
category_column = "cat"
strength_column = "str"
activity_column = "act"
section_pattern = 'Sec (?P<section>3\\.[123][a-f])'
"""
FLAGS = '[conditions_of_use.flags]\nreactant = "3.2a"\nproduce = "3.1a"\n'


def _load(tmp_path: Path, text: str = BASE + FLAGS) -> ConditionsSettings:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_conditions_settings(path)


def test_explicit_values_and_flags_in_section_order(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert (s.level, s.level_column, s.activity_column) == ("L1", "lvl", "act")
    assert s.flags == (("produce", "3.1a"), ("reactant", "3.2a"))
    assert s.section_pattern.search("Part Sec 3.2b").group("section") == "3.2b"  # type: ignore[union-attr]
    assert s.crosswalk_path.is_absolute()


def test_shipped_settings() -> None:
    s = get_conditions_settings()
    assert len(s.flags) == 15 and s.crosswalk_path.is_file()
    assert dict(s.flags)["ancillary"] == "3.3c"
    assert s.section_pattern.search("Part II Section 3.3 (a, b, c)") is None


def test_the_release_query_joins_the_activity_table() -> None:
    assert "/tri_submission_naics/tri_chem_activity/cas_registry_number/" in (
        get_tri_settings().release_path
    )


@pytest.mark.parametrize(
    ("flags", "message"),
    [
        ("[conditions_of_use.flags]\n", "at least one flag"),
        ('[conditions_of_use.flags]\na = "3.4a"\n', "flags.a must be a Form R section"),
        ('[conditions_of_use.flags]\na = ""\n', "flags"),
        ('[conditions_of_use.flags]\na = "3.2a"\nb = "3.2a"\n', "repeat a section"),
        ("", "flags"),
    ],
)
def test_invalid_flags(tmp_path: Path, flags: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, BASE + flags)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('level = "L1"', 'level = ""', "level"),
        ('section_column = "sec"', 'section_column = ""', "section_column"),
        ("(?P<section>", "(?P<other>", "named group 'section'"),
        ("(?P<section>3", "((((3", "section_pattern is not a valid"),
        ('crosswalk_path = "data/x.csv"\n', "", "crosswalk_path"),
    ],
)
def test_invalid_values_name_the_key(tmp_path: Path, old: str, new: str, message: str) -> None:
    text = BASE.replace(old, new, 1) + FLAGS
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, text)
