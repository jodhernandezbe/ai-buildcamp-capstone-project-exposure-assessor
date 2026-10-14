"""Typed loader for ``config/settings.toml``."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

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


@dataclass(frozen=True)
class PropertySpec:
    """One CompTox property to extract.

    Attributes:
        key: Key used in the lookup result, e.g. ``"vapor_pressure"``.
        name: CompTox ``propName`` to match exactly, e.g. ``"Vapor Pressure"``.
    """

    key: str
    name: str


@dataclass(frozen=True)
class ComptoxSettings:
    """EPA CompTox Chemicals Dashboard API settings.

    The API key itself is never stored here; only the environment variable that holds it.

    Attributes:
        base_url: Service root URL, without trailing slash.
        dtxsid_by_smiles_path: Path template appended to ``base_url``; contains ``{smiles}``.
        properties_by_dtxsid_path: Path template appended to ``base_url``; contains ``{dtxsid}``.
        api_key_header: Name of the HTTP header carrying the API key.
        api_key_env_var: Name of the environment variable holding the API key.
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
        properties: Properties to extract, in order.
    """

    base_url: str
    dtxsid_by_smiles_path: str
    properties_by_dtxsid_path: str
    api_key_header: str
    api_key_env_var: str
    delay_seconds: float
    timeout_seconds: float
    properties: tuple[PropertySpec, ...]

    @property
    def dtxsid_by_smiles_url(self) -> str:
        """Full URL template containing the ``{smiles}`` placeholder."""
        return self.base_url.rstrip("/") + self.dtxsid_by_smiles_path

    @property
    def properties_by_dtxsid_url(self) -> str:
        """Full URL template containing the ``{dtxsid}`` placeholder."""
        return self.base_url.rstrip("/") + self.properties_by_dtxsid_path


def _require_str(section: dict[str, object], key: str, name: str = "pubchem") -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}.{key} must be a non-empty string")
    return value


def _require_number(
    section: dict[str, object], key: str, *, minimum: float, name: str = "pubchem"
) -> float:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name}.{key} must be a number")
    if value < minimum or (minimum > 0 and value == 0):
        raise ValueError(f"{name}.{key} must be >= {minimum}")
    return float(value)


def _read_toml(path: Path | None) -> dict[str, object]:
    settings_path = path or DEFAULT_SETTINGS_PATH
    if not settings_path.is_file():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    with settings_path.open("rb") as handle:
        return tomllib.load(handle)


def _section(data: dict[str, object], name: str) -> dict[str, object]:
    raw = data.get(name)
    if not isinstance(raw, dict):
        raise ValueError(f"{name} section is missing")
    return {str(k): v for k, v in raw.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


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
    section = _section(_read_toml(path), "pubchem")
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


def _parse_properties(section: dict[str, object]) -> tuple[PropertySpec, ...]:
    raw = section.get("properties")
    if not isinstance(raw, list) or not raw:
        raise ValueError("comptox.properties must be a non-empty list")
    specs: list[PropertySpec] = []
    for item in cast(list[object], raw):
        if not isinstance(item, dict):
            raise ValueError("comptox.properties entries must be tables")
        entry = {str(k): v for k, v in cast(dict[object, object], item).items()}
        specs.append(
            PropertySpec(
                key=_require_str(entry, "key", "comptox.properties"),
                name=_require_str(entry, "name", "comptox.properties"),
            )
        )
    keys = [spec.key for spec in specs]
    if len(set(keys)) != len(keys):
        raise ValueError("comptox.properties keys must be unique")
    return tuple(specs)


def load_comptox_settings(path: Path | None = None) -> ComptoxSettings:
    """Load and validate CompTox settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Returns:
        The validated settings (delay and timeout in seconds).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    section = _section(_read_toml(path), "comptox")
    smiles_path = _require_str(section, "dtxsid_by_smiles_path", "comptox")
    if "{smiles}" not in smiles_path:
        raise ValueError("comptox.dtxsid_by_smiles_path must contain {smiles}")
    props_path = _require_str(section, "properties_by_dtxsid_path", "comptox")
    if "{dtxsid}" not in props_path:
        raise ValueError("comptox.properties_by_dtxsid_path must contain {dtxsid}")
    return ComptoxSettings(
        base_url=_require_str(section, "base_url", "comptox"),
        dtxsid_by_smiles_path=smiles_path,
        properties_by_dtxsid_path=props_path,
        api_key_header=_require_str(section, "api_key_header", "comptox"),
        api_key_env_var=_require_str(section, "api_key_env_var", "comptox"),
        delay_seconds=_require_number(section, "delay_seconds", minimum=0, name="comptox"),
        timeout_seconds=_require_number(section, "timeout_seconds", minimum=0.001, name="comptox"),
        properties=_parse_properties(section),
    )


@lru_cache(maxsize=1)
def get_comptox_settings() -> ComptoxSettings:
    """Return the cached CompTox settings from the default file."""
    return load_comptox_settings()
