"""Typed loader for ``config/settings.toml``."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

DEFAULT_SETTINGS_PATH = Path(__file__).parent / "settings.toml"


@dataclass(frozen=True)
class PropertySpec:
    """One CompTox property to extract.

    Attributes:
        key: Key used in the lookup result, e.g. ``"vapor_pressure"``.
        name: CompTox ``propName`` to match exactly, e.g. ``"Vapor Pressure"``.
        target_unit: Unit the value is converted to, e.g. ``"mmHg"``.
    """

    key: str
    name: str
    target_unit: str


@dataclass(frozen=True)
class MolecularWeightSpec:
    """Where CompTox reports molecular weight and in which units.

    Attributes:
        field: Field of the chemical detail response that holds it, e.g. ``"averageMass"``.
        unit: Unit the API reports it in (the response carries none), e.g. ``"g/mol"``.
        target_unit: Unit the value is converted to, e.g. ``"g/mol"``.
    """

    field: str
    unit: str
    target_unit: str


@dataclass(frozen=True)
class ToxicityValueSpec:
    """One CompTox ToxVal toxicity value to extract.

    Attributes:
        key: Key used in the lookup result, e.g. ``"rfd"``.
        types: Accepted ``toxvalType`` labels (exact match), e.g. ``("RfC",)``.
        routes: Accepted ``exposureRoute`` values, lower-case, e.g. ``("inhalation",)``. The
            first is the route the value applies to (reported to the user as the applied route).
        prefer: ``"lowest"`` or ``"highest"``: which value to take among the records of the
            best-ranked source (the most conservative one).
        target_unit: Unit the value is converted to, e.g. ``"mg/m^3"``.
    """

    key: str
    types: tuple[str, ...]
    routes: tuple[str, ...]
    prefer: Literal["lowest", "highest"]
    target_unit: str

    @property
    def applied_route(self) -> str:
        """Route the value applies to: the first accepted route."""
        return self.routes[0]


@dataclass(frozen=True)
class UnitSettings:
    """Unit-conversion settings.

    Attributes:
        aliases: Source unit spelling -> Pint-parsable unit string.
    """

    aliases: dict[str, str]


@dataclass(frozen=True)
class ComptoxSettings:
    """EPA CompTox Chemicals Dashboard API settings.

    The API key itself is never stored here; only the environment variable that holds it.

    Attributes:
        base_url: Service root URL, without trailing slash.
        dtxsid_by_cas_path: Path template appended to ``base_url``; contains ``{casrn}``.
        detail_by_dtxsid_path: Path template appended to ``base_url``; contains ``{dtxsid}``.
        properties_by_dtxsid_path: Path template appended to ``base_url``; contains ``{dtxsid}``.
        toxval_by_dtxsid_path: Path template appended to ``base_url``; contains ``{dtxsid}``.
        source_priority: ToxVal ``source`` names, most preferred first.
        api_key_header: Name of the HTTP header carrying the API key.
        api_key_env_var: Name of the environment variable holding the API key.
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
        molecular_weight: Where molecular weight is read from and its units.
        properties: Properties to extract, in order.
        toxicity_values: Toxicity values to extract, in order.
    """

    base_url: str
    dtxsid_by_cas_path: str
    detail_by_dtxsid_path: str
    properties_by_dtxsid_path: str
    toxval_by_dtxsid_path: str
    source_priority: tuple[str, ...]
    api_key_header: str
    api_key_env_var: str
    delay_seconds: float
    timeout_seconds: float
    molecular_weight: MolecularWeightSpec
    properties: tuple[PropertySpec, ...]
    toxicity_values: tuple[ToxicityValueSpec, ...]

    @property
    def dtxsid_by_cas_url(self) -> str:
        """Full URL template containing the ``{casrn}`` placeholder."""
        return self.base_url.rstrip("/") + self.dtxsid_by_cas_path

    @property
    def detail_by_dtxsid_url(self) -> str:
        """Full URL template containing the ``{dtxsid}`` placeholder."""
        return self.base_url.rstrip("/") + self.detail_by_dtxsid_path

    @property
    def properties_by_dtxsid_url(self) -> str:
        """Full URL template containing the ``{dtxsid}`` placeholder."""
        return self.base_url.rstrip("/") + self.properties_by_dtxsid_path

    @property
    def toxval_by_dtxsid_url(self) -> str:
        """Full URL template containing the ``{dtxsid}`` placeholder."""
        return self.base_url.rstrip("/") + self.toxval_by_dtxsid_path


def _require_str(section: dict[str, object], key: str, name: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}.{key} must be a non-empty string")
    return value


def _require_number(section: dict[str, object], key: str, *, minimum: float, name: str) -> float:
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


def _tables(section: dict[str, object], key: str) -> list[dict[str, object]]:
    """Return the non-empty array of tables ``comptox.<key>`` as plain dicts."""
    raw = section.get(key)
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"comptox.{key} must be a non-empty list")
    tables: list[dict[str, object]] = []
    for item in cast(list[object], raw):
        if not isinstance(item, dict):
            raise ValueError(f"comptox.{key} entries must be tables")
        tables.append({str(k): v for k, v in cast(dict[object, object], item).items()})
    return tables


def _require_unique(keys: list[str], where: str) -> None:
    if len(set(keys)) != len(keys):
        raise ValueError(f"{where} keys must be unique")


def _property_spec(entry: dict[str, object]) -> PropertySpec:
    where = "comptox.properties"
    return PropertySpec(
        key=_require_str(entry, "key", where),
        name=_require_str(entry, "name", where),
        target_unit=_require_str(entry, "target_unit", where),
    )


def _parse_properties(section: dict[str, object]) -> tuple[PropertySpec, ...]:
    specs = tuple(_property_spec(entry) for entry in _tables(section, "properties"))
    _require_unique([spec.key for spec in specs], "comptox.properties")
    return specs


def _parse_source_priority(section: dict[str, object]) -> tuple[str, ...]:
    raw = section.get("source_priority", [])
    if not isinstance(raw, list):
        raise ValueError("comptox.source_priority must be a list of strings")
    names = cast(list[object], raw)
    if not all(isinstance(n, str) and n.strip() for n in names):
        raise ValueError("comptox.source_priority must be a list of non-empty strings")
    return tuple(cast(list[str], names))


def _parse_molecular_weight(section: dict[str, object]) -> MolecularWeightSpec:
    raw = section.get("molecular_weight")
    if not isinstance(raw, dict):
        raise ValueError("comptox.molecular_weight must be a table")
    entry = {str(k): v for k, v in cast(dict[object, object], raw).items()}
    name = "comptox.molecular_weight"
    return MolecularWeightSpec(
        field=_require_str(entry, "field", name),
        unit=_require_str(entry, "unit", name),
        target_unit=_require_str(entry, "target_unit", name),
    )


def _string_list(entry: dict[str, object], key: str) -> tuple[str, ...]:
    value = entry.get(key)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(v, str) and v.strip() for v in cast(list[object], value))
    ):
        raise ValueError(f"comptox.toxicity_values.{key} must be a non-empty list of strings")
    return tuple(cast(list[str], value))


def _toxicity_spec(entry: dict[str, object]) -> ToxicityValueSpec:
    where = "comptox.toxicity_values"
    prefer = entry.get("prefer")
    if prefer not in ("lowest", "highest"):
        raise ValueError(f"{where}.prefer must be 'lowest' or 'highest'")
    return ToxicityValueSpec(
        key=_require_str(entry, "key", where),
        types=_string_list(entry, "types"),
        routes=tuple(route.strip().lower() for route in _string_list(entry, "routes")),
        prefer=prefer,
        target_unit=_require_str(entry, "target_unit", where),
    )


def _parse_toxicity_values(section: dict[str, object]) -> tuple[ToxicityValueSpec, ...]:
    specs = tuple(_toxicity_spec(entry) for entry in _tables(section, "toxicity_values"))
    _require_unique([spec.key for spec in specs], "comptox.toxicity_values")
    return specs


def _require_template(section: dict[str, object], key: str, placeholder: str) -> str:
    template = _require_str(section, key, "comptox")
    if placeholder not in template:
        raise ValueError(f"comptox.{key} must contain {placeholder}")
    return template


def _comptox_str(section: dict[str, object], key: str) -> str:
    return _require_str(section, key, "comptox")


def _comptox_seconds(section: dict[str, object], key: str, minimum: float) -> float:
    return _require_number(section, key, minimum=minimum, name="comptox")


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
    return ComptoxSettings(
        base_url=_comptox_str(section, "base_url"),
        dtxsid_by_cas_path=_require_template(section, "dtxsid_by_cas_path", "{casrn}"),
        detail_by_dtxsid_path=_require_template(section, "detail_by_dtxsid_path", "{dtxsid}"),
        properties_by_dtxsid_path=_require_template(
            section, "properties_by_dtxsid_path", "{dtxsid}"
        ),
        toxval_by_dtxsid_path=_require_template(section, "toxval_by_dtxsid_path", "{dtxsid}"),
        source_priority=_parse_source_priority(section),
        api_key_header=_comptox_str(section, "api_key_header"),
        api_key_env_var=_comptox_str(section, "api_key_env_var"),
        delay_seconds=_comptox_seconds(section, "delay_seconds", 0),
        timeout_seconds=_comptox_seconds(section, "timeout_seconds", 0.001),
        molecular_weight=_parse_molecular_weight(section),
        properties=_parse_properties(section),
        toxicity_values=_parse_toxicity_values(section),
    )


@lru_cache(maxsize=1)
def get_comptox_settings() -> ComptoxSettings:
    """Return the cached CompTox settings from the default file."""
    return load_comptox_settings()


def load_unit_settings(path: Path | None = None) -> UnitSettings:
    """Load and validate unit-conversion settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Returns:
        The alias table; empty if the file has no ``[units.aliases]`` table.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the alias table is not a table of non-empty strings.
    """
    data = _read_toml(path)
    units = data.get("units")
    if units is None:
        return UnitSettings(aliases={})
    if not isinstance(units, dict):
        raise ValueError("units must be a table")
    raw = cast(dict[str, object], units).get("aliases", {})
    if not isinstance(raw, dict):
        raise ValueError("units.aliases must be a table")
    aliases: dict[str, str] = {}
    for source, target in cast(dict[object, object], raw).items():
        if not isinstance(source, str) or not source.strip():
            raise ValueError("units.aliases keys must be non-empty strings")
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"units.aliases.{source} must be a non-empty string")
        aliases[source.strip()] = target.strip()
    return UnitSettings(aliases=aliases)


@lru_cache(maxsize=1)
def get_unit_settings() -> UnitSettings:
    """Return the cached unit settings from the default file."""
    return load_unit_settings()
