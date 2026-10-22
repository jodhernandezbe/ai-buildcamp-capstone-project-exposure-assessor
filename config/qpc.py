"""Typed loader for the ``[qpc]`` settings (Census plant capacity utilization baseline)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from config.parsing import (
    project_path,
    read_toml,
    require_int,
    require_number,
    require_str,
    section,
)

NAME = "qpc"


@dataclass(frozen=True)
class QpcSettings:
    """Where the QPC workbook is, what to look for in it and what values are plausible.

    Attributes:
        url_template: https URL with ``{year}`` and ``{quarter}`` slots.
        allowed_host: The only host the URL may point to.
        lag_quarters: Quarters before the current one whose release is downloaded.
        sheet_name: Tab holding the utilization table.
        code_header: Label of the NAICS code column (whitespace and case ignored).
        hours_header: Label of the average plant hours per week column.
        title_pattern: Regex with groups ``year`` and ``quarter`` matched on the sheet title.
        intro_sheet_name: Tab that states the NAICS edition.
        naics_edition: NAICS edition (a year) the workbook must state.
        titles_vintage_column: Column of the NAICS titles table holding a code's edition.
        naics_edition_pattern: Regex with group ``edition`` searched in the intro tab.
        min_hours: Hours must be greater than this (exclusive), in h/week.
        max_hours_per_week: Hours must be at most this, in h/week (168 = 24 h x 7 d).
        min_codes: Fewest four-digit codes a valid release yields.
        header_search_rows: How many rows from the top the header row may be.
        timeout_seconds: Time limit for the download, in s.
        max_bytes: Largest accepted download, in bytes.
        output_path: Parquet to write; absolute or resolved against the project root.
    """

    url_template: str
    allowed_host: str
    lag_quarters: int
    timeout_seconds: float
    max_bytes: int
    sheet_name: str
    code_header: str
    hours_header: str
    title_pattern: re.Pattern[str]
    intro_sheet_name: str
    naics_edition: int
    titles_vintage_column: str
    naics_edition_pattern: re.Pattern[str]
    header_search_rows: int
    min_hours: float
    max_hours_per_week: float
    min_codes: int
    output_path: Path


def _text(table: dict[str, object], key: str) -> str:
    return require_str(table, key, NAME).strip()


def _url_template(table: dict[str, object], host: str) -> str:
    template = _text(table, "url_template")
    parsed = urlparse(template)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise ValueError(f"{NAME}.url_template must be an https URL on {host}")
    if "{year}" not in template or "{quarter}" not in template:
        raise ValueError(f"{NAME}.url_template must contain {{year}} and {{quarter}}")
    return template


def _pattern(table: dict[str, object], key: str, group_names: tuple[str, ...]) -> re.Pattern[str]:
    try:
        compiled = re.compile(_text(table, key))
    except re.error as error:
        raise ValueError(f"{NAME}.{key} is not a valid regular expression: {error}") from error
    missing = [group for group in group_names if group not in compiled.groupindex]
    if missing:
        raise ValueError(f"{NAME}.{key} must have the named group {missing[0]!r}")
    return compiled


def _bounds(table: dict[str, object]) -> tuple[float, float]:
    low = require_number(table, "min_hours", minimum=0, name=NAME)
    high = require_number(table, "max_hours_per_week", minimum=1, name=NAME)
    if high <= low:
        raise ValueError(f"{NAME}.max_hours_per_week must be greater than {NAME}.min_hours")
    return low, high


def _source(table: dict[str, object]) -> tuple[str, str, int, float, int]:
    """url_template, allowed_host, lag_quarters, timeout_seconds, max_bytes."""
    host = _text(table, "allowed_host")
    return (
        _url_template(table, host),
        host,
        require_int(table, "lag_quarters", minimum=0, name=NAME),
        require_number(table, "timeout_seconds", minimum=0.001, name=NAME),
        require_int(table, "max_bytes", minimum=1, name=NAME),
    )


def _layout(
    table: dict[str, object],
) -> tuple[str, str, str, re.Pattern[str], str, int, str, re.Pattern[str], int]:
    """sheet_name .. header_search_rows: what to look for in the workbook."""
    return (
        _text(table, "sheet_name"),
        _text(table, "code_header"),
        _text(table, "hours_header"),
        _pattern(table, "title_pattern", ("year", "quarter")),
        _text(table, "intro_sheet_name"),
        require_int(table, "naics_edition", minimum=1900, name=NAME),
        _text(table, "titles_vintage_column"),
        _pattern(table, "naics_edition_pattern", ("edition",)),
        require_int(table, "header_search_rows", minimum=1, name=NAME),
    )


def _limits(table: dict[str, object]) -> tuple[float, float, int, Path]:
    """min_hours, max_hours_per_week, min_codes, output_path."""
    low, high = _bounds(table)
    return (
        low,
        high,
        require_int(table, "min_codes", minimum=1, name=NAME),
        project_path(table, "output_path", NAME),
    )


def load_qpc_settings(path: Path | None = None) -> QpcSettings:
    """Load and validate the QPC settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), NAME)
    return QpcSettings(*_source(table), *_layout(table), *_limits(table))


@lru_cache(maxsize=1)
def get_qpc_settings() -> QpcSettings:
    """Return the cached QPC settings from the default file."""
    return load_qpc_settings()
