"""Typed loader for ``config/settings.toml``."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_SETTINGS_PATH = Path(__file__).parent / "settings.toml"


@dataclass(frozen=True)
class PubChemSettings:
    """PubChem PUG REST settings.

    Attributes:
        base_url: Service root URL, without trailing slash.
        compound_property_path: Path template appended to ``base_url``; must contain
            ``{identifier}``.
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
    """

    base_url: str
    compound_property_path: str
    delay_seconds: float
    timeout_seconds: float

    @property
    def compound_property_url(self) -> str:
        """Full URL template containing the ``{identifier}`` placeholder."""
        return self.base_url.rstrip("/") + self.compound_property_path


def _require_str(section: dict[str, object], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"pubchem.{key} must be a non-empty string")
    return value


def _require_number(section: dict[str, object], key: str, *, minimum: float) -> float:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"pubchem.{key} must be a number")
    if value < minimum or (minimum > 0 and value == 0):
        raise ValueError(f"pubchem.{key} must be >= {minimum}")
    return float(value)


def load_settings(path: Path | None = None) -> PubChemSettings:
    """Load and validate PubChem settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Returns:
        The validated settings (delay and timeout in seconds).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    settings_path = path or DEFAULT_SETTINGS_PATH
    if not settings_path.is_file():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    with settings_path.open("rb") as handle:
        data = tomllib.load(handle)
    raw = data.get("pubchem")
    if not isinstance(raw, dict):
        raise ValueError("pubchem section is missing")
    section: dict[str, object] = {str(k): v for k, v in raw.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    path_template = _require_str(section, "compound_property_path")
    if "{identifier}" not in path_template:
        raise ValueError("pubchem.compound_property_path must contain {identifier}")
    return PubChemSettings(
        base_url=_require_str(section, "base_url"),
        compound_property_path=path_template,
        delay_seconds=_require_number(section, "delay_seconds", minimum=0),
        timeout_seconds=_require_number(section, "timeout_seconds", minimum=0.001),
    )


@lru_cache(maxsize=1)
def get_settings() -> PubChemSettings:
    """Return the cached settings from the default file."""
    return load_settings()
