"""Typed loader for the ``[user_values]`` settings (chemical benchmarks a user may enter).

Only chemistry quantities are listed: stack parameters are never asked for, because a missing
NEI row is covered by the PSTK and EPA global-default fall-backs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import cast

from config.parsing import read_toml, require_number, section, subtable
from config.stack import StackRange

USER_QUANTITIES = ("molecular_weight", "vapor_pressure", "density", "rfd", "rfc", "sf", "iur")


@dataclass(frozen=True)
class UserValueSettings:
    """Accepted units and plausible ranges for values a user may enter.

    Attributes:
        units: Quantity -> accepted entry units; the first is the target unit.
        ranges: Quantity -> plausible range in the target unit.
    """

    units: Mapping[str, tuple[str, ...]]
    ranges: Mapping[str, StackRange]


def _unit_list(raw: object, name: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{name} must be a non-empty list of units")
    items = cast(list[object], raw)
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise ValueError(f"{name} must hold non-empty unit strings")
    units = tuple(cast(str, item).strip() for item in items)
    if len(set(units)) != len(units):
        raise ValueError(f"{name} lists a unit more than once")
    return units


def _parse_units(table: dict[str, object]) -> dict[str, tuple[str, ...]]:
    raw = subtable(table, "units", "user_values")
    unknown = sorted(set(raw) - set(USER_QUANTITIES))
    if unknown:
        raise ValueError(f"user_values.units has unknown quantities: {', '.join(unknown)}")
    missing = [q for q in USER_QUANTITIES if q not in raw]
    if missing:
        raise ValueError(f"user_values.units lacks quantities: {', '.join(missing)}")
    return {q: _unit_list(raw[q], f"user_values.units.{q}") for q in USER_QUANTITIES}


def _bound(value: object, name: str) -> float:
    return require_number({"bound": value}, "bound", minimum=1e-12, name=name)


def _range(table: dict[str, object], key: str, name: str) -> StackRange:
    raw = table.get(key)
    if not isinstance(raw, list) or len(cast(list[object], raw)) != 2:
        raise ValueError(f"{name}.{key} must be [minimum, maximum]")
    low = _bound(cast(list[object], raw)[0], f"{name}.{key}")
    high = _bound(cast(list[object], raw)[1], f"{name}.{key}")
    if low >= high:
        raise ValueError(f"{name}.{key} minimum must be below maximum")
    return StackRange(minimum=low, maximum=high)


def _parse_ranges(table: dict[str, object]) -> dict[str, StackRange]:
    raw = subtable(table, "ranges", "user_values")
    unknown = sorted(set(raw) - set(USER_QUANTITIES))
    if unknown:
        raise ValueError(f"user_values.ranges has unknown quantities: {', '.join(unknown)}")
    missing = [q for q in USER_QUANTITIES if q not in raw]
    if missing:
        raise ValueError(f"user_values.ranges lacks quantities: {', '.join(missing)}")
    return {q: _range(raw, q, "user_values.ranges") for q in USER_QUANTITIES}


def load_user_value_settings(path: Path | None = None) -> UserValueSettings:
    """Load and validate the user-value settings.

    Args:
        path: Settings file; defaults to the ``settings.toml`` shipped in ``config/``.

    Returns:
        The validated settings. Ranges are in each quantity's target unit.

    Raises:
        FileNotFoundError: If the settings file does not exist.
        ValueError: If a key is missing or invalid; the message names the key.
    """
    table = section(read_toml(path), "user_values")
    return UserValueSettings(
        units=MappingProxyType(_parse_units(table)),
        ranges=MappingProxyType(_parse_ranges(table)),
    )


@lru_cache(maxsize=1)
def get_user_value_settings() -> UserValueSettings:
    """Return the cached user-value settings from the default file."""
    return load_user_value_settings()
