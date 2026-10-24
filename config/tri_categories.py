"""Typed loader for the ``[tri_categories]`` settings (TRI category member list)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config.parsing import project_path, read_toml, require_str, section

NAME = "tri_categories"


@dataclass(frozen=True)
class TriCategoriesSettings:
    """Where the TRI category member list is and what its columns are called.

    Attributes:
        path: CSV of category members; absolute or resolved against the project root.
        cas_column: Column holding the member's CAS number.
        code_column: Column holding the category code (N420, or a CAS number without hyphens).
        category_name_column: Column holding the category name.
        member_name_column: Column holding the member's name (display only, never a key).
        type_column: Column holding the member's chemical type.
        organic_value: Value of ``type_column`` for an organic member.
    """

    path: Path
    cas_column: str
    code_column: str
    category_name_column: str
    member_name_column: str
    type_column: str
    organic_value: str


def _text(table: dict[str, object], key: str) -> str:
    return require_str(table, key, NAME).strip()


def load_tri_categories_settings(path: Path | None = None) -> TriCategoriesSettings:
    """Load and validate the TRI category settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), NAME)
    return TriCategoriesSettings(
        path=project_path(table, "path", NAME),
        cas_column=_text(table, "cas_column"),
        code_column=_text(table, "code_column"),
        category_name_column=_text(table, "category_name_column"),
        member_name_column=_text(table, "member_name_column"),
        type_column=_text(table, "type_column"),
        organic_value=_text(table, "organic_value"),
    )


@lru_cache(maxsize=1)
def get_tri_categories_settings() -> TriCategoriesSettings:
    """Return the cached TRI category settings from the default file."""
    return load_tri_categories_settings()
