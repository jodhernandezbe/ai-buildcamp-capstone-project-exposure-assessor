"""Tests for the ``[tri_categories]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.tri_categories import (
    TriCategoriesSettings,
    get_tri_categories_settings,
    load_tri_categories_settings,
)

GOOD = {
    "path": '"data/x.csv"',
    "cas_column": '"CAS"',
    "code_column": '"CODE"',
    "category_name_column": '"CAT"',
    "member_name_column": '"NAME"',
    "type_column": '"TYPE"',
    "organic_value": '"Organic"',
}


def _load(tmp_path: Path, **override: str) -> TriCategoriesSettings:
    values = {**GOOD, **override}
    body = "\n".join(f"{key} = {value}" for key, value in values.items())
    path = tmp_path / "settings.toml"
    path.write_text(f"[tri_categories]\n{body}\n", encoding="utf-8")
    return load_tri_categories_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert (s.cas_column, s.code_column, s.organic_value) == ("CAS", "CODE", "Organic")
    assert s.path.is_absolute() and s.path.name == "x.csv"


def test_shipped_settings_point_at_the_committed_file() -> None:
    assert get_tri_categories_settings().path.is_file()


@pytest.mark.parametrize("key", list(GOOD))
def test_missing_key_is_named(tmp_path: Path, key: str) -> None:
    body = "\n".join(f"{k} = {v}" for k, v in GOOD.items() if k != key)
    path = tmp_path / "settings.toml"
    path.write_text(f"[tri_categories]\n{body}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=key):
        load_tri_categories_settings(path)


def test_missing_section_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text("[other]\na = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="tri_categories"):
        load_tri_categories_settings(path)
