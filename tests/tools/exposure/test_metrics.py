"""Tests for calculate_exposure_metrics (the tool; the maths is tested in models and helpers)."""

from __future__ import annotations

import pytest

from tools.exposure.metrics import calculate_exposure_metrics

STACK: dict[str, object] = {
    "stack_height": 30.0,
    "stack_diameter": 2.0,
    "exit_velocity": 10.0,
    "exit_temperature": 400.0,
    "source": "NEI",
    "scc": None,
    "warnings": [],
}
MET: dict[str, object] = {
    "wind_speed": 4.0,
    "wind_direction": 270.0,
    "stability_class": "D",
    "ambient_temperature": 288.0,
    "source": "Open-Meteo era5 reanalysis 2022",
    "warnings": [],
}
POP: dict[str, object] = {
    "total_population": 1000,
    "age_distribution": {"0-4": 10.0, "5-17": 20.0, "18-64": 50.0, "65+": 20.0},
    "source": "Census ACS 2023 5-year (DP05), 3 tracts",
    "warnings": [],
}
TOX: dict[str, object] = {"rfc": 0.01, "iur": 1e-5}


def _args(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "emission_rate": 0.5,
        "stacks": [STACK],
        "meteorology": MET,
        "population": POP,
        "toxicity": TOX,
    }
    base.update(changes)
    return base


def test_schema() -> None:
    assert calculate_exposure_metrics.name == "calculate_exposure_metrics"
    assert set(calculate_exposure_metrics.args) == {
        "emission_rate",
        "stacks",
        "meteorology",
        "population",
        "toxicity",
    }


def test_description_carries_the_decisions() -> None:
    text = " ".join(calculate_exposure_metrics.description.split())
    for phrase in (
        "SCREEN3",
        "flat terrain",
        "no building downwash",
        "no mixing-height limit",
        "54 combinations",
        "100 m to 10 km",
        "ALL of a facility's candidate stacks",
        "never a subset, never one call per stack",
        "report the `range`",
        "One call per facility",
        "WORST CASE",
        "REPRESENTATIVE",
        "annual average",
        "may fall where nobody lives",
        "g/s",
        "ug/m3",
        "mg/(kg*day)",
        "A null number means it could not be computed",
        "nothing is ever defaulted",
        "must be reported, not filled in",
        "children breathe more per kg",
        "not regulatory determinations",
    ):
        assert phrase in text, phrase


def test_returns_the_documented_fields() -> None:
    facility = calculate_exposure_metrics.invoke(_args())
    for key in ("results", "range", "stacks_given", "stacks_evaluated", "warnings"):
        assert key in facility
    (result,) = facility["results"]
    assert result["stack_number"] == 1 and result["stack_height"] == STACK["stack_height"]
    for key in (
        "max_concentration",
        "max_concentration_1h",
        "distance_m",
        "stability_class",
        "wind_speed",
        "effective_release_height",
        "hq",
        "cancer_risk",
        "add",
        "add_band",
        "add_by_band",
        "representative",
        "warnings",
    ):
        assert key in result
    assert result["max_concentration"] > 0 and result["hq"] > 0 and result["cancer_risk"] > 0
    assert result["representative"]["max_concentration"] <= result["max_concentration"]
    assert result["add"] == max(result["add_by_band"].values())
    assert facility["range"]["hq"]["low"] == facility["range"]["hq"]["high"] == result["hq"]


def test_evaluates_every_stack_given_in_one_call() -> None:
    tall = {**STACK, "stack_height": 60.0}
    facility = calculate_exposure_metrics.invoke(_args(stacks=[STACK, tall, STACK]))
    assert (facility["stacks_given"], facility["stacks_evaluated"]) == (3, 3)
    assert [r["stack_number"] for r in facility["results"]] == [1, 2, 3]
    assert facility["range"]["max_concentration"]["low_stack"] == 2


def test_accepts_the_shapes_the_other_tools_return() -> None:
    """A stack candidate, Meteorology, Population and a Toxicity built from chemical properties."""
    properties = {"rfc": 0.02, "iur": None, "rfd": 0.1, "sf": None}
    toxicity = {"rfc": properties["rfc"], "iur": properties["iur"]}
    (result,) = calculate_exposure_metrics.invoke(_args(toxicity=toxicity))["results"]
    assert result["hq"] is not None
    assert result["cancer_risk"] is None
    assert any("IUR" in w for w in result["warnings"])


def test_a_stack_without_values_gives_nulls_and_says_why() -> None:
    empty = {
        **STACK,
        "stack_height": None,
        "stack_diameter": None,
        "exit_velocity": None,
        "exit_temperature": None,
        "source": None,
    }
    facility = calculate_exposure_metrics.invoke(_args(stacks=[empty, STACK]))
    result = facility["results"][0]
    assert result["max_concentration"] is None and result["hq"] is None
    assert "stack has no value" in result["warnings"][0]
    assert facility["results"][1]["max_concentration"] is not None
    assert facility["stacks_evaluated"] == 1


@pytest.mark.parametrize("rate", [-1.0])
def test_an_invalid_emission_rate_gives_nulls(rate: float) -> None:
    (result,) = calculate_exposure_metrics.invoke(_args(emission_rate=rate))["results"]
    assert result["max_concentration"] is None
    assert "emission rate" in result["warnings"][0]
