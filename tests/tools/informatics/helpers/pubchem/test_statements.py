"""Tests for reading one PubChem statement (synthetic numbers; the forms are PubChem's)."""

from __future__ import annotations

import pytest

from tools.informatics.helpers.pubchem.record import Statement
from tools.informatics.helpers.pubchem.statements import Reading, read_statement


def _read(text: str, unit: str | None = None) -> Reading | str:
    return read_statement(Statement(text, unit))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("7 mm Hg at 25 °C", Reading(7.0, "mm Hg", 25.0)),
        ("7 mmHg", Reading(7.0, "mmHg", None)),
        ("7 [mm Hg] @25 °C", Reading(7.0, "mm Hg", 25.0)),
        ("0.5 g/cu cm at 20 °C", Reading(0.5, "g/cu cm", 20.0)),
        ("Vapor pressure, kPa at 21.5 °C: 3.5", Reading(3.5, "kPa", 21.5)),
        ("Density, kg/cu m: 500", Reading(500.0, "kg/cu m", None)),
        ("2.5e1 mmHg AT 20 C", Reading(25.0, "mmHg", 20.0)),
    ],
)
def test_clear_statements_are_read(text: str, expected: Reading) -> None:
    assert _read(text) == expected


def test_fahrenheit_is_converted_to_celsius() -> None:
    reading = _read("7 mmHg at 68 °F")
    assert isinstance(reading, Reading) and reading.celsius == pytest.approx(20.0)


def test_structured_unit_with_a_lone_number() -> None:
    assert _read("100.5", "g/mol") == Reading(100.5, "g/mol", None)


@pytest.mark.parametrize("text", ["abc", "1-2", "", "1,5"])
def test_structured_unit_with_anything_but_a_number_is_refused(text: str) -> None:
    assert isinstance(_read(text, "g/mol"), str)


@pytest.mark.parametrize(
    "text",
    [
        "1-2 mmHg",
        "> 1 mmHg",
        "< 1 mmHg",
        "~1 mmHg",
        "about 1 mmHg",
        "1 mmHg (estimated)",
        "7 mmHg at 25 °C ; 9 mmHg at 30 °C",
        "7 mmHg at 25 °C, 9 mmHg at 30 °C",
        "Vapor pressure: 7 mm Hg at 20 °C",
        "0.5",
        "0.5 at 32 °F",
        "0.5 @25 °C",
        "5 at",
        "Relative density (water = 1): 0.5",
        "Liquid density (at saturation pressure; 15.6 °C), kg/cu m: 500 /from table/",
        "0.5 g/cu cm at 25 °C (p>1 atm)",
        "1,000 mmHg",
        "7 mmHg at 25 K",
        "see the table",
        "nan mmHg",
        "inf mmHg",
    ],
)
def test_unclear_statements_are_refused_with_a_reason(text: str) -> None:
    outcome = _read(text)
    assert isinstance(outcome, str) and outcome
