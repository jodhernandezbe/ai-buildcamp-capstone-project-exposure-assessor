"""Tests for the ppm to mg/m^3 conversion."""

from __future__ import annotations

import pytest

from models.chemistry.air_units import ppm_to_mg_per_m3


def test_benzene_like_conversion() -> None:
    assert ppm_to_mg_per_m3(1.0, 78.11, 24.45) == pytest.approx(3.1947, rel=1e-4)


def test_zero_ppm_is_zero() -> None:
    assert ppm_to_mg_per_m3(0.0, 100.0, 24.45) == 0.0
