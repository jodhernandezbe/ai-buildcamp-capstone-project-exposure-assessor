"""Tests for tools.emissions.helpers.rate."""

from __future__ import annotations

import math

import pytest

from commons.units import UnitConversionError
from config.loader import EmissionsSettings, get_unit_settings, load_emissions_settings
from tools.emissions.helpers.rate import operating_hours_per_year, to_emission_rate

ALIASES = {"Pounds": "pound"}
KG_PER_POUND = 0.45359237


def test_pounds_per_year_to_grams_per_second() -> None:
    # 8760 lb over 8760 h: one pound per hour = 453.59237 g / 3600 s.
    rate = to_emission_rate(8760.0, "Pounds", 8760.0, ALIASES)
    assert rate == pytest.approx(453.59237 / 3600.0)


def test_fewer_hours_raises_the_rate() -> None:
    full = to_emission_rate(1000.0, "Pounds", 8760.0, ALIASES)
    assert to_emission_rate(1000.0, "Pounds", 4380.0, ALIASES) == pytest.approx(2 * full)


def test_other_mass_units() -> None:
    assert to_emission_rate(1000.0, "kg", 1000.0) == pytest.approx(1000.0 / 3600.0)
    assert to_emission_rate(1.0, "tonne", 1.0) == pytest.approx(1_000_000.0 / 3600.0)


def test_zero_release_is_zero_rate() -> None:
    assert to_emission_rate(0.0, "Pounds", 8760.0, ALIASES) == 0.0


@pytest.mark.parametrize("unit", ["furlongs", "", "m^3", "mg/m3"])
def test_unknown_or_non_mass_unit_fails(unit: str) -> None:
    with pytest.raises(UnitConversionError):
        to_emission_rate(1.0, unit, 8760.0, ALIASES)


@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_non_finite_value_fails(value: float) -> None:
    with pytest.raises(UnitConversionError):
        to_emission_rate(value, "Pounds", 8760.0, ALIASES)


def test_negative_value_and_bad_hours_fail() -> None:
    with pytest.raises(ValueError, match="annual_mass_kg"):
        to_emission_rate(-1.0, "Pounds", 8760.0, ALIASES)
    for hours in (0.0, -1.0):
        with pytest.raises(ValueError, match="operating_hours_per_year"):
            to_emission_rate(1.0, "Pounds", hours, ALIASES)


def test_hours_come_from_settings() -> None:
    assert operating_hours_per_year(EmissionsSettings(operating_hours_per_year=2000.0)) == 2000.0
    assert operating_hours_per_year(load_emissions_settings()) == 8760.0


def test_changing_the_setting_changes_the_rate() -> None:
    aliases = get_unit_settings().aliases
    rates = [
        to_emission_rate(1000.0, "Pounds", operating_hours_per_year(EmissionsSettings(h)), aliases)
        for h in (8760.0, 4380.0)
    ]
    assert rates[1] == pytest.approx(2 * rates[0])
    assert rates[0] == pytest.approx(1000.0 * KG_PER_POUND * 1000.0 / (8760.0 * 3600.0))
