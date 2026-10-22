"""Tests for the ``[industry]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.industry import IndustrySettings, load_industry_settings

TEXT = """
[industry]
submission_naics_path = "/S/{doc_ctrl_num}/JSON"
title_path = "/T/{naics_code}/JSON"
code_field = "c"
primary_field = "p"
primary_value = "Y"
sequence_field = "q"
origin_field = "o"
reported_value = "Rep"
assigned_value = "Asg"
title_field = "t"
placeholder_codes = ["999999", " 000000 "]
titles_path = "data/naics_titles.csv"
titles_code_column = "code"
titles_title_column = "title"
"""


def _load(tmp_path: Path, text: str = TEXT) -> IndustrySettings:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_industry_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert s.submission_naics_path == "/S/{doc_ctrl_num}/JSON"
    assert s.title_path == "/T/{naics_code}/JSON"
    assert (s.code_field, s.primary_field, s.primary_value, s.sequence_field) == (
        "c",
        "p",
        "Y",
        "q",
    )
    assert (s.origin_field, s.reported_value, s.assigned_value, s.title_field) == (
        "o",
        "Rep",
        "Asg",
        "t",
    )
    assert s.placeholder_codes == ("999999", "000000")
    assert s.titles_path.is_absolute() and s.titles_path.parts[-2:] == ("data", "naics_titles.csv")
    assert (s.titles_code_column, s.titles_title_column) == ("code", "title")


def test_default_file_loads() -> None:
    s = load_industry_settings()
    assert (
        s.submission_naics_path
        == "/tri_submission_naics/primary_ind/1/doc_ctrl_num/{doc_ctrl_num}/JSON"
    )
    assert "{naics_code}" in s.title_path
    assert s.placeholder_codes == ("999999",)
    assert (s.code_field, s.title_field, s.origin_field) == ("naics_code", "naics_desc", "source")
    assert (s.reported_value, s.assigned_value) == ("Reported", "ASSIGNED")
    assert s.titles_path.is_file()
    assert (s.titles_code_column, s.titles_title_column) == ("naics_code", "naics_title")


def test_no_placeholders_is_allowed(tmp_path: Path) -> None:
    assert _load(tmp_path, TEXT.replace('["999999", " 000000 "]', "[]")).placeholder_codes == ()


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ('"/S/{doc_ctrl_num}/JSON"', '"/S/x/JSON"', "submission_naics_path"),
        ('"/S/{doc_ctrl_num}/JSON"', '"S/{doc_ctrl_num}"', "submission_naics_path"),
        ('"/T/{naics_code}/JSON"', '"/T/x/JSON"', "title_path"),
        ('code_field = "c"', "", "industry.code_field"),
        ('primary_field = "p"', 'primary_field = ""', "industry.primary_field"),
        ('primary_value = "Y"', "primary_value = 1", "industry.primary_value"),
        ('sequence_field = "q"', "", "industry.sequence_field"),
        ('origin_field = "o"', "", "industry.origin_field"),
        ('reported_value = "Rep"', 'reported_value = ""', "industry.reported_value"),
        ('assigned_value = "Asg"', "", "industry.assigned_value"),
        ('title_field = "t"', "", "industry.title_field"),
        ('["999999", " 000000 "]', '["abc"]', "placeholder_codes"),
        ('["999999", " 000000 "]', '["99-99"]', "placeholder_codes"),
        ('["999999", " 000000 "]', '"999999"', "placeholder_codes"),
        ('titles_path = "data/naics_titles.csv"', 'titles_path = ""', "industry.titles_path"),
        ('titles_code_column = "code"', "", "industry.titles_code_column"),
        (
            'titles_title_column = "title"',
            'titles_title_column = " "',
            "industry.titles_title_column",
        ),
    ],
)
def test_invalid_entries_name_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    assert old in TEXT
    with pytest.raises(ValueError, match=key):
        _load(tmp_path, TEXT.replace(old, new, 1))


def test_section_and_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="industry section"):
        _load(tmp_path, "[other]\nx = 1\n")
    with pytest.raises(FileNotFoundError):
        load_industry_settings(tmp_path / "absent.toml")
