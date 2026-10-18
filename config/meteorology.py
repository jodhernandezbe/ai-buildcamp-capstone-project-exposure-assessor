"""Typed loader for the ``[meteorology]`` settings (meteorological conditions tool)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from config.parsing import (
    as_table,
    read_toml,
    require_int,
    require_number,
    require_str,
    section,
    subtable,
)
from config.policy import RequestPolicy, parse_policy

HOURLY_QUANTITIES = (
    "temperature",
    "wind_speed",
    "wind_direction",
    "solar_radiation",
    "cloud_cover",
    "low_cloud_cover",
    "is_day",
)
STABILITY_CLASSES = ("A", "B", "C", "D", "E", "F")
_FULL_CIRCLE = 360.0
_MAX_DECIMALS = 6


@dataclass(frozen=True)
class ScreeningDefault:
    """Conditions returned when no usable data are available.

    Attributes:
        wind_speed: m/s.
        wind_direction: Degrees clockwise from north, the direction the wind blows from.
        stability_class: Pasquill-Gifford class, "A" to "F".
        ambient_temperature: K.
    """

    wind_speed: float
    wind_direction: float
    stability_class: str
    ambient_temperature: float


@dataclass(frozen=True)
class ArchiveRequest:
    """What is asked of the archive and what it must answer with.

    Attributes:
        base_url: Archive root URL, without trailing slash.
        archive_path: Path of the archive endpoint, starting with ``/``.
        model: Reanalysis product requested (the ``models`` parameter).
        wind_speed_unit: Value of the ``wind_speed_unit`` parameter.
        timezone: Value of the ``timezone`` parameter.
        coordinate_decimals: Decimals the coordinates are rounded to in the request.
        variables: Quantity (see ``HOURLY_QUANTITIES``) -> archive variable name.
        units: Quantity -> unit the archive must report it in.
    """

    base_url: str
    archive_path: str
    model: str
    wind_speed_unit: str
    timezone: str
    coordinate_decimals: int
    variables: Mapping[str, str]
    units: Mapping[str, str]

    @property
    def url(self) -> str:
        """Full URL of the archive endpoint."""
        return self.base_url.rstrip("/") + self.archive_path


@dataclass(frozen=True)
class YearWindow:
    """Which reporting years can be requested.

    Attributes:
        default_year: Reporting year used when none is given.
        first_year: First year the archive covers.
        archive_lag_days: Days the archive lags behind the present.
    """

    default_year: int
    first_year: int
    archive_lag_days: int


@dataclass(frozen=True)
class SummaryRules:
    """How a year of hours is summarized.

    Attributes:
        minimum_wind_speed: Lowest annual wind speed reported, m/s.
        sector_width: Wind direction sector width, degrees (divides 360).
    """

    minimum_wind_speed: float
    sector_width: float


@dataclass(frozen=True)
class MeteorologySettings:
    """Meteorology settings, grouped by who uses them."""

    request: ArchiveRequest
    policy: RequestPolicy
    years: YearWindow
    summary: SummaryRules
    screening_default: ScreeningDefault


def _strings(table: dict[str, object], name: str, *, allow_empty: bool) -> Mapping[str, str]:
    """Return one string per hourly quantity; raises naming a missing or invalid entry."""
    unknown = sorted(set(table) - set(HOURLY_QUANTITIES))
    if unknown:
        raise ValueError(f"{name} has unknown quantities: {', '.join(unknown)}")
    values: dict[str, str] = {}
    for quantity in HOURLY_QUANTITIES:
        value = table.get(quantity)
        if not isinstance(value, str) or (not allow_empty and not value.strip()):
            raise ValueError(f"{name}.{quantity} must be a string")
        values[quantity] = value.strip()
    return MappingProxyType(values)


def _sector_width(table: dict[str, object]) -> float:
    width = require_number(table, "sector_width", minimum=1e-9, name="meteorology")
    sectors = _FULL_CIRCLE / width
    if width > _FULL_CIRCLE or abs(sectors - round(sectors)) > 1e-9:
        raise ValueError("meteorology.sector_width must divide 360 evenly")
    return width


def _decimals(table: dict[str, object]) -> int:
    decimals = require_int(table, "coordinate_decimals", minimum=0, name="meteorology")
    if decimals > _MAX_DECIMALS:
        raise ValueError(f"meteorology.coordinate_decimals must be at most {_MAX_DECIMALS}")
    return decimals


def _years(table: dict[str, object]) -> YearWindow:
    first = require_int(table, "first_year", minimum=1, name="meteorology")
    default = require_int(table, "default_year", minimum=1, name="meteorology")
    if first > default:
        raise ValueError("meteorology.first_year must not be later than meteorology.default_year")
    lag = require_int(table, "archive_lag_days", minimum=0, name="meteorology")
    return YearWindow(default_year=default, first_year=first, archive_lag_days=lag)


def _screening_default(table: dict[str, object]) -> ScreeningDefault:
    name = "meteorology.screening_default"
    block = subtable(table, "screening_default", "meteorology")
    stability = require_str(block, "stability_class", name).strip().upper()
    if stability not in STABILITY_CLASSES:
        raise ValueError(f"{name}.stability_class must be one of A to F")
    direction = require_number(block, "wind_direction", minimum=0, name=name)
    if direction >= _FULL_CIRCLE:
        raise ValueError(f"{name}.wind_direction must be below 360")
    return ScreeningDefault(
        wind_speed=require_number(block, "wind_speed", minimum=1e-9, name=name),
        wind_direction=direction,
        stability_class=stability,
        ambient_temperature=require_number(block, "ambient_temperature", minimum=1e-9, name=name),
    )


def _archive_path(table: dict[str, object]) -> str:
    path = require_str(table, "archive_path", "meteorology").strip()
    if not path.startswith("/"):
        raise ValueError("meteorology.archive_path must start with /")
    return path


def _per_quantity(table: dict[str, object], key: str, *, allow_empty: bool) -> Mapping[str, str]:
    name = f"meteorology.{key}"
    return _strings(as_table(table.get(key), name), name, allow_empty=allow_empty)


def _request(table: dict[str, object]) -> ArchiveRequest:
    name = "meteorology"
    return ArchiveRequest(
        base_url=require_str(table, "base_url", name).strip(),
        archive_path=_archive_path(table),
        model=require_str(table, "model", name).strip(),
        wind_speed_unit=require_str(table, "wind_speed_unit", name).strip(),
        timezone=require_str(table, "timezone", name).strip(),
        coordinate_decimals=_decimals(table),
        variables=_per_quantity(table, "variables", allow_empty=False),
        units=_per_quantity(table, "units", allow_empty=True),
    )


def _summary(table: dict[str, object]) -> SummaryRules:
    minimum = require_number(table, "minimum_wind_speed", minimum=1e-9, name="meteorology")
    return SummaryRules(minimum_wind_speed=minimum, sector_width=_sector_width(table))


def load_meteorology_settings(path: Path | None = None) -> MeteorologySettings:
    """Load and validate the meteorology settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), "meteorology")
    return MeteorologySettings(
        request=_request(table),
        policy=parse_policy(table, "meteorology"),
        years=_years(table),
        summary=_summary(table),
        screening_default=_screening_default(table),
    )


@lru_cache(maxsize=1)
def get_meteorology_settings() -> MeteorologySettings:
    """Return the cached meteorology settings from the default file."""
    return load_meteorology_settings()
