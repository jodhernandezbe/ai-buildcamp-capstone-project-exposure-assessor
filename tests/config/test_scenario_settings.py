"""Tests for the ``[scenario]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.scenario import GROUPS, get_scenario_settings, load_scenario_settings

TEXT = """
[scenario]
receptor_fraction = 0.5
max_receptors = 10

[scenario.pathways]
a = "Air → Inhalation → People"

[scenario.quantities]
hq = "Hazard quotient"

[scenario.factors.height]
group = "source"
label = "Height"
unit = "m"
"""


def test_explicit_values(tmp_path: Path) -> None:
    s = load_scenario_settings(_write(tmp_path, TEXT))
    assert (s.receptor_fraction, s.max_receptors) == (0.5, 10)
    assert s.pathways == {"a": "Air → Inhalation → People"}
    assert s.quantities == {"hq": "Hazard quotient"}
    assert (s.factors["height"].group, s.factors["height"].unit) == ("source", "m")


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("receptor_fraction = 0.5", "receptor_fraction = 0.0", "receptor_fraction"),
        ("receptor_fraction = 0.5", "receptor_fraction = 1.5", "receptor_fraction"),
        ("max_receptors = 10", "max_receptors = 0", "max_receptors"),
        ('group = "source"', 'group = "elsewhere"', "scenario.factors.height.group"),
        ('unit = "m"', "unit = 3", "scenario.factors.height.unit"),
        ('label = "Height"', 'label = ""', "scenario.factors.height"),
    ],
)
def test_invalid_values_are_refused(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_scenario_settings(_write(tmp_path, TEXT.replace(old, new)))


def test_the_shipped_settings_define_every_group_and_both_pathways() -> None:
    s = get_scenario_settings()
    assert {f.group for f in s.factors.values()} == set(GROUPS)
    assert set(s.pathways) == {"community_inhalation", "worker_inhalation"}
    assert set(s.quantities) == {"hq", "cancer_risk", "oel_ratio"}
