"""Tests for the exposure metric tools."""

from __future__ import annotations

import pytest

from tools.exposure.metrics import calculate_exposure_metrics, get_population_receptors


def test_population_schema() -> None:
    assert get_population_receptors.name == "get_population_receptors"
    assert set(get_population_receptors.args) == {"latitude", "longitude", "radius_km"}


def test_population_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        get_population_receptors.invoke({"latitude": 0.0, "longitude": 0.0, "radius_km": 1.0})


def test_exposure_metrics_schema() -> None:
    assert calculate_exposure_metrics.name == "calculate_exposure_metrics"
    assert set(calculate_exposure_metrics.args) == {
        "emission_rate",
        "stack_params",
        "meteorology",
        "population",
        "toxicity",
    }
    assert calculate_exposure_metrics.description
