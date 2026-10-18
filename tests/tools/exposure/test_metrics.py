"""Tests for the exposure metric tools."""

from __future__ import annotations

from tools.exposure.metrics import calculate_exposure_metrics


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
