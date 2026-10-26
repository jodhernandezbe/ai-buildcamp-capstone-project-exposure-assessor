"""Tests for the report's value formatting (same text as the dashboard, never a computed value)."""

from __future__ import annotations

import math

import pytest

from api.services.report.values import ValueFormat

FMT = ValueFormat(digits=3, not_reported="not reported")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.8200, "0.82"),
        (48213.0, "48200"),
        (0.0000123456, "1.23 × 10⁻⁵"),
        (123456.0, "1.23 × 10⁵"),
        (1e-4, "1 × 10⁻⁴"),
        (0.0, "0"),
        (2.0, "2"),
    ],
)
def test_number_significant_digits(value: float, expected: str) -> None:
    assert FMT.number(value) == expected


def test_number_with_unit() -> None:
    assert FMT.number(0.03, "mg/m³") == "0.03 mg/m³"


@pytest.mark.parametrize("value", [None, math.nan, math.inf, -math.inf])
def test_absent_or_non_finite_is_not_reported(value: float | None) -> None:
    assert FMT.number(value, "mg/m³") == "not reported"
    assert FMT.reported(value, "lb") == "not reported"


def test_bool_is_not_a_number() -> None:
    assert FMT.number(True) == "not reported"  # pyright: ignore[reportArgumentType]


def test_absent_with_reason() -> None:
    assert FMT.number(None, reason="user declined") == "not reported (user declined)"
    assert FMT.absent(None) == "not reported"


def test_reported_is_not_rounded() -> None:
    assert FMT.reported(1234.5678, "lb") == "1234.5678 lb"
    assert FMT.reported(8760.0) == "8760"


def test_count_text_and_flag() -> None:
    assert FMT.count(48213) == "48,213"
    assert FMT.count(None) == "not reported"
    assert FMT.text("  ") == "not reported"
    assert FMT.text(" CompTox ") == "CompTox"
    assert (FMT.flag(True), FMT.flag(False), FMT.flag(None)) == ("Yes", "No", "not reported")


def test_span() -> None:
    assert FMT.span(0.1, 0.1) == "0.1"
    assert FMT.span(0.1, 0.25, "µg/m³") == "0.1 – 0.25 µg/m³"
    assert FMT.span(None, None) == "not reported"
