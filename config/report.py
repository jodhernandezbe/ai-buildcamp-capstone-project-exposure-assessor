"""Typed loader for ``[ui.report]``: the fixed text of the Word assessment report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.parsing import project_path, read_toml, require_str, section, subtable

_NAME = "ui.report"
_SUFFIX = ".docx"
_LOGO_SUFFIX = ".png"
_PAGE_FIELDS = ("{page}", "{pages}")
_FIELDS = ("{cas}", "{date}")


@dataclass(frozen=True)
class ReportHeadings:
    """The eight section headings, in report order."""

    summary: str
    chemical: str
    sources: str
    releases: str
    exposure: str
    risk: str
    uncertainties: str
    assessor: str

    def ordered(self) -> tuple[str, ...]:
        """The headings in the order the report numbers them (1 to 8)."""
        return (
            self.summary,
            self.chemical,
            self.sources,
            self.releases,
            self.exposure,
            self.risk,
            self.uncertainties,
            self.assessor,
        )


@dataclass(frozen=True)
class ReportSettings:
    """Fixed report text.

    Attributes:
        title: Title printed at the top of the report.
        disclaimer: Screening-level disclaimer under the title.
        assessor_note: Note labelling section 8 as written by the AI assistant.
        no_assessor_summary: Section 8 text when the thread has no assistant message.
        empty_section: Text of a section with no data.
        not_reported: Text printed for an absent value.
        file_name: File-name pattern with ``{cas}`` and ``{date}``, ending in ``.docx``.
        brand: App name printed in the page header beside the logo.
        logo: PNG of the app logo for the page header (an existing file).
        page_label: Page footer with ``{page}`` and ``{pages}`` once each.
        headings: The eight section headings.
    """

    title: str
    disclaimer: str
    assessor_note: str
    no_assessor_summary: str
    empty_section: str
    not_reported: str
    file_name: str
    brand: str
    logo: Path
    page_label: str
    headings: ReportHeadings


def _text(table: dict[str, object], key: str, name: str = _NAME) -> str:
    return require_str(table, key, name).strip()


def _file_name(table: dict[str, object]) -> str:
    pattern = _text(table, "file_name")
    if not pattern.endswith(_SUFFIX) or not all(field in pattern for field in _FIELDS):
        raise ValueError(f"{_NAME}.file_name must contain {{cas}} and {{date}} and end in .docx")
    return pattern


def _logo(table: dict[str, object]) -> Path:
    path = project_path(table, "logo", _NAME)
    if path.suffix.lower() != _LOGO_SUFFIX:
        raise ValueError(f"{_NAME}.logo must be a .png file")
    if not path.is_file():
        raise FileNotFoundError(f"{_NAME}.logo does not exist: {path}")
    return path


def _page_label(table: dict[str, object]) -> str:
    label = _text(table, "page_label")
    if any(label.count(field) != 1 for field in _PAGE_FIELDS):
        raise ValueError(f"{_NAME}.page_label must contain {{page}} and {{pages}} once each")
    return label


def _headings(table: dict[str, object]) -> ReportHeadings:
    name = f"{_NAME}.headings"
    sub = subtable(table, "headings", _NAME)
    keys = ReportHeadings.__dataclass_fields__
    return ReportHeadings(**{key: _text(sub, key, name) for key in keys})


def parse_report(ui_table: dict[str, object]) -> ReportSettings:
    """Validate the ``report`` table of an already-read ``[ui]`` table.

    Raises:
        ValueError: If a key is missing or invalid; the message names the key.
        FileNotFoundError: If the logo file does not exist.
    """
    table = subtable(ui_table, "report", "ui")
    return ReportSettings(
        title=_text(table, "title"),
        disclaimer=_text(table, "disclaimer"),
        assessor_note=_text(table, "assessor_note"),
        no_assessor_summary=_text(table, "no_assessor_summary"),
        empty_section=_text(table, "empty_section"),
        not_reported=_text(table, "not_reported"),
        file_name=_file_name(table),
        brand=_text(table, "brand"),
        logo=_logo(table),
        page_label=_page_label(table),
        headings=_headings(table),
    )


def load_report_settings(path: Path | None = None) -> ReportSettings:
    """Load and validate the report text alone (``config.ui`` loads it with the rest of [ui]).

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the settings file or the logo does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    return parse_report(section(read_toml(path), "ui"))
