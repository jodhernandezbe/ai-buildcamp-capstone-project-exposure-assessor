"""Tests for the ``[ui.report]`` settings loader (fixed text of the Word report)."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.report import load_report_settings
from config.ui import get_ui_settings

REPORT = """
[ui.report]
title = "Title"
disclaimer = "Disclaimer"
assessor_note = "Note"
no_assessor_summary = "None available"
empty_section = "Empty"
not_reported = "absent"
file_name = "report-{cas}-{date}.docx"
brand = "Brand"
logo = "api/assets/report-logo.png"
page_label = "Page {page} of {pages}"

[ui.report.headings]
summary = "H1"
chemical = "H2"
sources = "H3"
releases = "H4"
exposure = "H5"
risk = "H6"
uncertainties = "H7"
assessor = "H8"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_values(tmp_path: Path) -> None:
    settings = load_report_settings(_write(tmp_path, REPORT))
    assert settings.title == "Title"
    assert settings.not_reported == "absent"
    assert settings.file_name == "report-{cas}-{date}.docx"
    assert settings.headings.ordered() == ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")


def test_shipped_settings_load() -> None:
    settings = get_ui_settings().report
    assert len(set(settings.headings.ordered())) == 8
    assert settings.file_name.endswith(".docx")


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ('assessor = "H8"', "", "headings.assessor"),
        ('title = "Title"', 'title = "  "', "title"),
        ('not_reported = "absent"', "not_reported = 0", "not_reported"),
        ('file_name = "report-{cas}-{date}.docx"', 'file_name = "report-{cas}.docx"', "file_name"),
        ('file_name = "report-{cas}-{date}.docx"', 'file_name = "r-{cas}-{date}.pdf"', "file_name"),
        ('brand = "Brand"', "", "brand"),
        ('logo = "api/assets/report-logo.png"', 'logo = "frontend/public/logo.svg"', "logo"),
        ('page_label = "Page {page} of {pages}"', 'page_label = "Page {page}"', "page_label"),
        (
            'page_label = "Page {page} of {pages}"',
            'page_label = "{page} {page} {pages}"',
            "page_label",
        ),
    ],
)
def test_invalid_entry(tmp_path: Path, old: str, new: str, key: str) -> None:
    with pytest.raises(ValueError, match=key):
        load_report_settings(_write(tmp_path, REPORT.replace(old, new)))


def test_logo_resolves_against_the_project_root(tmp_path: Path) -> None:
    settings = load_report_settings(_write(tmp_path, REPORT))
    assert settings.logo.is_absolute()
    assert settings.logo.is_file()
    assert settings.page_label == "Page {page} of {pages}"


def test_missing_logo_raises(tmp_path: Path) -> None:
    text = REPORT.replace("report-logo.png", "no-such-logo.png")
    with pytest.raises(FileNotFoundError, match="ui.report.logo"):
        load_report_settings(_write(tmp_path, text))


def test_missing_section(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ui.report"):
        load_report_settings(_write(tmp_path, "[ui]\nhost = 'x'\n"))
