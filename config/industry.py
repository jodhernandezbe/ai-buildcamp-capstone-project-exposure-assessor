"""Typed loader for the ``[industry]`` settings (facility industry tool)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import names, read_toml, require_str, section


@dataclass(frozen=True)
class IndustrySettings:
    """Where a TRI submission's primary NAICS code and its title are read from.

    Attributes:
        submission_naics_path: Path template with ``{doc_ctrl_num}``; the submission's primary
            NAICS rows.
        title_path: Path template with ``{naics_code}``; the code's reference row.
        code_field: Response field holding the NAICS code.
        primary_field: Response field flagging the primary code.
        primary_value: Value of ``primary_field`` that marks a primary code.
        sequence_field: Response field ordering the codes of a submission.
        origin_field: Response field saying who gave the code.
        reported_value: Value of ``origin_field`` for a code the facility reported.
        assigned_value: Value of ``origin_field`` for a code EPA assigned.
        title_field: Response field holding the code's title.
        placeholder_codes: Codes that are not industries and are never returned.
    """

    submission_naics_path: str
    title_path: str
    code_field: str
    primary_field: str
    primary_value: str
    sequence_field: str
    origin_field: str
    reported_value: str
    assigned_value: str
    title_field: str
    placeholder_codes: tuple[str, ...]


def _template(table: dict[str, object], key: str, slot: str) -> str:
    template = require_str(table, key, "industry").strip()
    if not template.startswith("/") or slot not in template:
        raise ValueError(f"industry.{key} must start with / and contain {slot}")
    return template


def _placeholders(table: dict[str, object]) -> tuple[str, ...]:
    codes = names(table, "placeholder_codes", "industry", allow_empty=True)
    bad = [code for code in codes if not code.isascii() or not code.isdigit()]
    if bad:
        raise ValueError(f"industry.placeholder_codes must be digit strings, got {bad[0]!r}")
    return codes


def _text(table: dict[str, object], key: str) -> str:
    return require_str(table, key, "industry").strip()


def load_industry_settings(path: Path | None = None) -> IndustrySettings:
    """Load and validate the industry settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), "industry")
    return IndustrySettings(
        submission_naics_path=_template(table, "submission_naics_path", "{doc_ctrl_num}"),
        title_path=_template(table, "title_path", "{naics_code}"),
        code_field=_text(table, "code_field"),
        primary_field=_text(table, "primary_field"),
        primary_value=_text(table, "primary_value"),
        sequence_field=_text(table, "sequence_field"),
        origin_field=_text(table, "origin_field"),
        reported_value=_text(table, "reported_value"),
        assigned_value=_text(table, "assigned_value"),
        title_field=_text(table, "title_field"),
        placeholder_codes=_placeholders(table),
    )


@lru_cache(maxsize=1)
def get_industry_settings() -> IndustrySettings:
    """Return the cached industry settings from the default file."""
    return load_industry_settings()
