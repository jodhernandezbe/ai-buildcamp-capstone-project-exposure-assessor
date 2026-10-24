"""Tests for checking values a user enters for a missing quantity."""

from __future__ import annotations

import math

import pytest

from config.loader import get_unit_settings
from config.user_values import UserValueSettings, get_user_value_settings
from tools.user_values import CheckedValue, check_entered_value

SETTINGS: UserValueSettings = get_user_value_settings()
ALIASES = get_unit_settings().aliases


def _check(quantity: str, number: object, unit: str) -> CheckedValue:
    return check_entered_value(quantity, number, unit, SETTINGS, ALIASES)


def test_accepted_value_converts_to_target_unit() -> None:
    result = _check("vapor_pressure", 760, "torr")
    assert result.reason is None
    assert result.value == pytest.approx(760.0, rel=1e-6)


def test_pascal_converts_to_mmhg() -> None:
    result = _check("vapor_pressure", 101325, "Pa")
    assert result.value == pytest.approx(760.0, rel=1e-4)


def test_reciprocal_iur_is_converted_by_the_unit_ratio() -> None:
    result = _check("iur", 0.002, "1/(mg/m^3)")
    assert result.value == pytest.approx(2e-6, rel=1e-9)


def test_reciprocal_iur_in_target_unit_is_unchanged() -> None:
    result = _check("iur", 2e-6, "1/(ug/m^3)")
    assert result.value == pytest.approx(2e-6, rel=1e-12)


def test_target_unit_is_kept_as_is() -> None:
    result = _check("rfc", 0.5, "mg/m^3")
    assert result.value == pytest.approx(0.5)


@pytest.mark.parametrize("bad", [True, False])
def test_boolean_is_never_a_number(bad: bool) -> None:
    result = _check("density", bad, "g/cm^3")
    assert result.value is None
    assert "finite number" in (result.reason or "")


@pytest.mark.parametrize("bad", ["12", None, [1], {"v": 1}])
def test_non_numeric_entry_is_rejected(bad: object) -> None:
    result = _check("density", bad, "g/cm^3")
    assert result.value is None
    assert result.reason is not None


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_number_is_rejected(bad: float) -> None:
    result = _check("density", bad, "g/cm^3")
    assert result.value is None


def test_value_above_range_is_rejected_not_clipped() -> None:
    result = _check("density", 4500, "g/cm^3")
    assert result.value is None
    assert "outside that range" in (result.reason or "")


def test_value_below_range_is_rejected_not_clipped() -> None:
    result = _check("density", 0.0001, "g/cm^3")
    assert result.value is None


def test_unit_of_another_quantity_is_rejected() -> None:
    result = _check("rfc", 10, "mmHg")
    assert result.value is None
    assert "accepted units" in (result.reason or "")


def test_unlisted_unit_is_rejected_even_if_it_converts() -> None:
    result = _check("density", 10, "km")
    assert result.value is None


def test_unknown_unit_string_is_rejected() -> None:
    result = _check("density", 1.0, "not-a-unit")
    assert result.value is None


def test_unknown_quantity_is_rejected() -> None:
    result = check_entered_value("bogus", 1.0, "m", SETTINGS, ALIASES)
    assert result.value is None
    assert "not a quantity" in (result.reason or "")


def test_pressure_converts_to_the_target_unit() -> None:
    result = _check("vapor_pressure", 1, "atm")
    assert result.value == pytest.approx(760.0, rel=1e-6)
