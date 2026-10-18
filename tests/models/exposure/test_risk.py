"""Tests for models.exposure.risk."""

from __future__ import annotations

import pytest

from models.exposure.risk import (
    calculate_cancer_risk,
    calculate_emission_rate,
    calculate_hazard_quotient,
)


def test_emission_rate_continuous() -> None:
    assert calculate_emission_rate(8760.0) == pytest.approx(1000.0 / 3600.0)


def test_emission_rate_partial_hours() -> None:
    assert calculate_emission_rate(100.0, 1000.0) == pytest.approx(100.0 * 1000.0 / 3_600_000.0)


def test_hazard_quotient() -> None:
    assert calculate_hazard_quotient(0.5, 0.25) == pytest.approx(2.0)


def test_cancer_risk() -> None:
    assert calculate_cancer_risk(2.0, 1e-6) == pytest.approx(2e-6)


def test_invalid() -> None:
    with pytest.raises(ValueError):
        calculate_emission_rate(-1.0)
    with pytest.raises(ValueError):
        calculate_emission_rate(1.0, 0.0)
    with pytest.raises(ValueError):
        calculate_hazard_quotient(1.0, 0.0)
    with pytest.raises(ValueError):
        calculate_cancer_risk(1.0, -1.0)
