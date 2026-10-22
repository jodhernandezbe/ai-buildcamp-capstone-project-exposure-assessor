"""Tests for the ``[qpc]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.qpc import QpcSettings, get_qpc_settings, load_qpc_settings

GOOD = {
    "url_template": '"https://h.example/{year}/q{quarter}.xlsx"',
    "allowed_host": '"h.example"',
    "lag_quarters": "2",
    "sheet_name": '"S"',
    "code_header": '"Code"',
    "hours_header": '"Hours"',
    "title_pattern": "'(?P<year>\\d{4}) Q(?P<quarter>[1-4])'",
    "intro_sheet_name": '"Intro"',
    "naics_edition": "2022",
    "titles_vintage_column": '"vintage"',
    "naics_edition_pattern": "'(?P<edition>\\d{4}) ed'",
    "min_hours": "0",
    "max_hours_per_week": "168",
    "min_codes": "3",
    "header_search_rows": "10",
    "timeout_seconds": "5",
    "max_bytes": "1000",
    "output_path": '"data/x.parquet"',
}


def _load(tmp_path: Path, **override: str) -> QpcSettings:
    values = {**GOOD, **override}
    body = "\n".join(f"{key} = {value}" for key, value in values.items())
    path = tmp_path / "settings.toml"
    path.write_text(f"[qpc]\n{body}\n", encoding="utf-8")
    return load_qpc_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert (s.lag_quarters, s.naics_edition, s.max_hours_per_week) == (2, 2022, 168.0)
    assert s.title_pattern.search("2026 Q2") is not None
    assert s.output_path.name == "x.parquet" and s.output_path.is_absolute()


def test_shipped_settings_load() -> None:
    s = get_qpc_settings()
    assert s.lag_quarters == 2
    assert s.allowed_host == "www2.census.gov"
    assert s.output_path.name == "census_qpc_baseline.parquet"


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("url_template", '"http://h.example/{year}/q{quarter}.xlsx"', "https URL on h.example"),
        ("url_template", '"https://other.example/{year}/q{quarter}.xlsx"', "https URL on"),
        ("url_template", '"https://h.example/{year}.xlsx"', r"\{quarter\}"),
        ("url_template", '"https://h.example/q{quarter}.xlsx"', r"\{year\}"),
        ("lag_quarters", "-1", "lag_quarters"),
        ("lag_quarters", "true", "lag_quarters"),
        ("title_pattern", "'(unclosed'", "title_pattern is not a valid"),
        ("title_pattern", "'(?P<year>\\d{4})'", "named group 'quarter'"),
        ("naics_edition_pattern", "'\\d{4}'", "named group 'edition'"),
        ("max_hours_per_week", "0", "max_hours_per_week"),
        ("max_hours_per_week", "nan", "max_hours_per_week"),
        ("max_hours_per_week", "true", "max_hours_per_week"),
        ("min_hours", "-1", "min_hours"),
        ("min_codes", "0", "min_codes"),
        ("timeout_seconds", "0", "timeout_seconds"),
        ("max_bytes", "0", "max_bytes"),
        ("sheet_name", '""', "sheet_name"),
    ],
)
def test_invalid_values_name_the_key(tmp_path: Path, key: str, value: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, **{key: value})


def test_hours_upper_bound_must_exceed_lower(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="greater than"):
        _load(tmp_path, min_hours="200")
