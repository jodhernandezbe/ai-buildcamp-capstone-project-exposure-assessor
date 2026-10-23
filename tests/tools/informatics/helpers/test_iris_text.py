"""Tests for the strict reader of the IRIS endpoint's value text."""

from __future__ import annotations

import pytest

from tools.informatics.helpers.iris_text import read_iris_value

UNITS = ("mg/m3",)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("5 mg/m3", 5.0),
        ("0.5 mg/m3", 0.5),
        ("2 x 10 -5 mg/m3", 0.00002),
        ("4 x 10 -3 mg/m3", 0.004),
        ("1.5 x 10 2 mg/m3", 150.0),
        ("  7 x 10 +1 mg/m3  ", 70.0),
        ("3 × 10^-4 mg/m3", 0.0003),
    ],
)
def test_readable_text(text: str, expected: float) -> None:
    assert read_iris_value(text, UNITS) == (expected, "mg/m3")


@pytest.mark.parametrize(
    "text",
    [
        "1-2 mg/m3",
        "1 - 2 mg/m3",
        "> 1 mg/m3",
        "< 1 mg/m3",
        "~1 mg/m3",
        "5",
        "5 mg/m3\n6 mg/m3",
        "5 mg/m3 or 6 mg/m3",
        "5 mg/kg-day",
        "5 MG/M3",
        "0 mg/m3",
        "0 x 10 -3 mg/m3",
        "-5 mg/m3",
        "1 x 10 400 mg/m3",
        "x 10 -3 mg/m3",
        "mg/m3",
        "",
        "-",
    ],
)
def test_text_that_cannot_be_read_exactly_is_refused(text: str) -> None:
    assert read_iris_value(text, UNITS) is None


@pytest.mark.parametrize("value", [None, 5, 5.0, True, ["5 mg/m3"]])
def test_non_text_is_refused(value: object) -> None:
    assert read_iris_value(value, UNITS) is None


def test_several_units_may_be_accepted() -> None:
    assert read_iris_value("5 mg/kg-day", ("mg/m3", "mg/kg-day")) == (5.0, "mg/kg-day")
