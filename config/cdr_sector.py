"""Typed loader for the ``[cdr_sector]`` settings (CDR industrial sector by NAICS code)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import project_path, read_toml, require_int, require_str, section

NAME = "cdr_sector"


@dataclass(frozen=True)
class CdrSectorSettings:
    """Where the NAICS to CDR industrial sector crosswalk is and how it is read.

    Attributes:
        crosswalk_path: CSV of NAICS prefix to industrial sector; absolute or project-relative.
        prefix_column: Column with the NAICS prefix (a digit string).
        code_column: Column with the sector code, e.g. ``"IS21"``.
        title_column: Column with the sector name.
        edition_column: Column with the NAICS edition the prefix belongs to.
        min_digits: Shortest prefix tried when matching a facility's code.
        max_digits: Longest prefix accepted, in the file and for a facility.
    """

    crosswalk_path: Path
    prefix_column: str
    code_column: str
    title_column: str
    edition_column: str
    min_digits: int
    max_digits: int


def load_cdr_sector_settings(path: Path | None = None) -> CdrSectorSettings:
    """Load and validate the CDR sector settings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), NAME)
    low = require_int(table, "min_digits", minimum=1, name=NAME)
    high = require_int(table, "max_digits", minimum=1, name=NAME)
    if low > high:
        raise ValueError(f"{NAME}.min_digits must be at most {NAME}.max_digits")
    return CdrSectorSettings(
        crosswalk_path=project_path(table, "crosswalk_path", NAME),
        prefix_column=require_str(table, "prefix_column", NAME).strip(),
        code_column=require_str(table, "code_column", NAME).strip(),
        title_column=require_str(table, "title_column", NAME).strip(),
        edition_column=require_str(table, "edition_column", NAME).strip(),
        min_digits=low,
        max_digits=high,
    )


@lru_cache(maxsize=1)
def get_cdr_sector_settings() -> CdrSectorSettings:
    """Return the cached CDR sector settings from the default file."""
    return load_cdr_sector_settings()
