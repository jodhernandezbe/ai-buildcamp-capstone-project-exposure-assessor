"""Tests for the local NAICS title table (synthetic codes and titles)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from config.industry import IndustrySettings, load_industry_settings
from tests.tools.emissions.records import emission_record
from tools.emissions.helpers.naics_titles import naics_titles, with_titles
from tools.schemas import EmissionRecord

SETTINGS = load_industry_settings()
TABLE = (
    "naics_code,naics_title,vintage\n111111,Synthetic Farming,2022\n222222, Spaced   Title ,2017\n"
)


def _table(tmp_path: Path, text: str = TABLE, name: str = "titles.csv") -> IndustrySettings:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return replace(SETTINGS, titles_path=path)


def test_reads_codes_and_titles(tmp_path: Path) -> None:
    titles = naics_titles(_table(tmp_path))
    assert titles["111111"] == "Synthetic Farming"
    assert titles["222222"] == "Spaced Title"  # whitespace normalised
    assert "333333" not in titles


def test_the_table_is_read_only(tmp_path: Path) -> None:
    titles = naics_titles(_table(tmp_path))
    with pytest.raises(TypeError):
        titles["444444"] = "x"  # type: ignore[index]


def test_a_duplicate_code_keeps_the_first_title(tmp_path: Path) -> None:
    text = TABLE + "111111,Later Farming,2017\n"
    assert naics_titles(_table(tmp_path, text, "dup.csv"))["111111"] == "Synthetic Farming"


@pytest.mark.parametrize(
    "text",
    [
        "naics_code,naics_title\nabc,Not A Code\n,Blank Code\n111111,\n111111,   \n",
    ],
)
def test_bad_rows_are_skipped(tmp_path: Path, text: str) -> None:
    assert dict(naics_titles(_table(tmp_path, text, "bad.csv"))) == {}


def test_a_missing_file_or_column_is_a_setup_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        naics_titles(replace(SETTINGS, titles_path=tmp_path / "absent.csv"))
    with pytest.raises(ValueError, match="naics_title"):
        naics_titles(_table(tmp_path, "naics_code,other\n111111,x\n", "cols.csv"))


def test_the_shipped_table_has_the_six_digit_codes() -> None:
    titles = naics_titles(SETTINGS)
    assert titles["324110"] == "Petroleum Refineries"
    assert all(len(code) == 6 for code in titles)
    assert len(titles) > 1000


def test_with_titles_fills_known_codes_and_keeps_the_rest_null() -> None:
    known: EmissionRecord = {**emission_record("A", 1.0), "naics_code": "111111"}
    unknown: EmissionRecord = {**emission_record("B", 1.0), "naics_code": "999998"}
    short: EmissionRecord = {**emission_record("C", 1.0), "naics_code": "11"}
    none = emission_record("D", 1.0)
    titled = with_titles([known, unknown, short, none], {"111111": "Synthetic Farming"})
    assert [r["naics_title"] for r in titled] == ["Synthetic Farming", None, None, None]
    assert known["naics_title"] is None  # the inputs are not changed
