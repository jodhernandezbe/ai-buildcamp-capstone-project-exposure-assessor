"""The runtime the web program runs with is built from configuration."""

from __future__ import annotations

from api.dependencies import get_runtime
from config.population import get_population_settings
from config.ui import get_ui_settings


def test_the_workspace_rules_come_from_settings() -> None:
    rules = get_runtime().workspace_rules
    assert rules is not None
    assert rules.thresholds == get_ui_settings().thresholds
    assert rules.coordinate_tolerance_deg == get_ui_settings().map.coordinate_tolerance_deg
    assert rules.default_radius_km == get_population_settings().default_radius_km
