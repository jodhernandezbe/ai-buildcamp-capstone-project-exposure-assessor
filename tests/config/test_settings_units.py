"""The shipped settings must only name units the converter understands."""

from __future__ import annotations

import pytest

from commons.units import convert
from config.loader import get_comptox_settings, get_unit_settings


def test_configured_units_parse_and_aliases_are_valid() -> None:
    settings = get_comptox_settings()
    aliases = get_unit_settings().aliases
    targets = [p.target_unit for p in settings.properties]
    targets += [t.target_unit for t in settings.toxicity_values]
    mass = settings.molecular_weight
    targets += [mass.unit, mass.target_unit]
    for unit in targets:
        assert convert(1.0, unit, unit, aliases) == pytest.approx(1.0)
    for source, target in aliases.items():
        assert convert(1.0, source, target, aliases) == pytest.approx(1.0)


def test_configured_alias_spellings_convert_to_targets() -> None:
    aliases = get_unit_settings().aliases
    assert convert(1.0, "ug/m3", "mg/m^3", aliases) == pytest.approx(0.001)
    assert convert(1.0, "mg/kg-day", "mg/(kg*day)", aliases) == pytest.approx(1.0)
    assert convert(1.0, "(ug/m3)-1", "1/(ug/m^3)", aliases) == pytest.approx(1.0)
    assert convert(1.0, "(mg/kg-day)-1", "1/(mg/(kg*day))", aliases) == pytest.approx(1.0)
