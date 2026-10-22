"""Annual release quantity -> average emission rate."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from commons.units import convert
from config.loader import EmissionsSettings
from models.exposure.risk import calculate_emission_rate


@dataclass(frozen=True)
class OperatingHours:
    """Hours a source operates per year (h/yr) and where that figure came from."""

    hours_per_year: float
    source: str


HoursFor = Callable[[str | None], OperatingHours]
"""Operating hours of a source from its primary NAICS code (None when it has none)."""


def operating_hours_per_year(settings: EmissionsSettings) -> float:
    """Return the operating hours per year to assume for a source, in hours per year (h/yr).

    This is the configured default (``[emissions]`` in ``config/settings.toml``), used for every
    source that has no industry-specific hours (see ``plant_hours.PlantHours``, which is given
    this value as its fallback).

    Args:
        settings: The emissions settings.

    Returns:
        Operating hours per year, h/yr.
    """
    return settings.operating_hours_per_year


def fixed_hours(settings: EmissionsSettings) -> HoursFor:
    """A resolver that gives every source the configured default hours."""
    hours = operating_hours_per_year(settings)
    fixed = OperatingHours(hours, f"default {hours:g} h/yr (configured)")
    return lambda _naics_code: fixed


def to_emission_rate(
    value: float,
    unit: str,
    hours: float,
    aliases: Mapping[str, str] | None = None,
) -> float:
    """Convert an annual release quantity to an average emission rate.

    Args:
        value: Quantity released per year, in ``unit`` per year. Finite and non-negative.
        unit: Mass unit as reported by the source, e.g. "Pounds".
        hours: Operating hours per year, h/yr. Positive.
        aliases: Source unit spelling -> Pint-parsable unit string.

    Returns:
        Emission rate in grams per second (g/s).

    Raises:
        UnitConversionError: If ``unit`` is unknown or not a mass, or ``value`` is not finite.
        ValueError: If ``value`` is negative or ``hours`` is not positive.
    """
    kilograms = convert(value, unit, "kg", aliases)
    return calculate_emission_rate(kilograms, hours)
