"""Annual release quantity -> average emission rate."""

from __future__ import annotations

from collections.abc import Mapping

from commons.units import convert
from config.loader import EmissionsSettings
from models.risk import calculate_emission_rate


def operating_hours_per_year(settings: EmissionsSettings) -> float:
    """Return the operating hours per year to assume for a source, in hours per year (h/yr).

    Today this is the single configured value for every source (``[emissions]`` in
    ``config/settings.toml``). It is the one place that decides the hours, so a more robust
    rule (by facility, sector or reported operating days) can be added here without
    changing callers.

    Args:
        settings: The emissions settings.

    Returns:
        Operating hours per year, h/yr.
    """
    return settings.operating_hours_per_year


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
