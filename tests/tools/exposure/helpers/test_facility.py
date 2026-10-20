"""Tests for tools.exposure.helpers.facility (synthetic round-number inputs)."""

from __future__ import annotations

import math
from typing import cast

from config.exposure import load_exposure_settings
from tools.exposure.helpers.assessment import assess_exposure
from tools.exposure.helpers.facility import assess_facility
from tools.schemas import (
    ExposureRange,
    FacilityExposure,
    Meteorology,
    Population,
    RangeEntry,
    StackParameters,
    Toxicity,
)

SETTINGS = load_exposure_settings()
Q = 0.5  # g/s
MET = Meteorology(
    wind_speed=4.0,
    wind_direction=270.0,
    stability_class="D",
    ambient_temperature=288.0,
    source="Open-Meteo era5 reanalysis 2022",
    warnings=[],
)
POP = Population(
    total_population=1000,
    age_distribution={"0-4": 10.0, "5-17": 20.0, "18-64": 50.0, "65+": 20.0},
    source="Census ACS 2023",
    warnings=[],
)
TOX = Toxicity(rfc=0.01, iur=1e-5)


def _stack(height: float | None = 30.0, temperature: float | None = 400.0) -> StackParameters:
    return StackParameters(
        stack_height=height,
        stack_diameter=2.0,
        exit_velocity=10.0,
        exit_temperature=temperature,
        source="NEI",
        scc=None,
        warnings=[],
    )


def _run(stacks: object, q: float = Q, tox: Toxicity = TOX) -> FacilityExposure:
    return assess_facility(q, stacks, MET, POP, tox, SETTINGS)


def _range(result: FacilityExposure) -> ExposureRange:
    assert result["range"] is not None
    return result["range"]


def _entry(result: FacilityExposure, quantity: str) -> RangeEntry:
    entry = cast(RangeEntry | None, _range(result).get(quantity))
    assert entry is not None
    return entry


def test_each_stack_equals_its_single_evaluation() -> None:
    stacks = [
        _stack(height) for height in (10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0)
    ]
    result = _run(stacks)
    assert [r["stack_number"] for r in result["results"]] == list(range(1, 11))
    for stack, got in zip(stacks, result["results"], strict=True):
        alone = assess_exposure(Q, stack, MET, POP, TOX, SETTINGS)
        assert got["max_concentration"] == alone["max_concentration"]
        assert got["hq"] == alone["hq"] and got["warnings"] == alone["warnings"]
        assert got["stack_height"] == stack["stack_height"]
    assert (result["stacks_given"], result["stacks_evaluated"]) == (10, 10)
    assert result["warnings"] == []


def test_range_names_the_stack_behind_each_end() -> None:
    result = _run([_stack(30.0), _stack(10.0), _stack(60.0)])
    concentration = _entry(result, "max_concentration")
    by_stack = {r["stack_number"]: float(r["max_concentration"] or 0.0) for r in result["results"]}
    assert concentration["low"] == min(by_stack.values()) == by_stack[concentration["low_stack"]]
    assert concentration["high"] == max(by_stack.values()) == by_stack[concentration["high_stack"]]
    assert concentration["high_stack"] == 2  # the 10 m stack: taller stacks never give more
    assert _entry(result, "hq")["high_stack"] == 2


def test_range_covers_the_representative_case_too() -> None:
    result = _run([_stack(30.0), _stack(10.0), _stack(60.0)])
    typical = _range(result)["representative"]["max_concentration"]
    values = [float(r["representative"]["max_concentration"] or 0.0) for r in result["results"]]
    assert typical is not None
    assert (typical["low"], typical["high"]) == (min(values), max(values))
    assert typical["high"] <= _entry(result, "max_concentration")["high"]


def test_a_bad_stack_does_not_stop_the_others() -> None:
    result = _run([_stack(), _stack(temperature=None), _stack(50.0)])
    assert result["results"][1]["max_concentration"] is None
    assert "exit_temperature" in result["results"][1]["warnings"][0]
    assert result["results"][0]["max_concentration"] is not None
    assert (result["stacks_given"], result["stacks_evaluated"]) == (3, 2)
    assert "1 of 3 stacks could not be evaluated" in result["warnings"][0]
    assert _entry(result, "max_concentration")["low_stack"] in (1, 3)


def test_no_stacks_gives_no_results_and_says_so() -> None:
    empties: list[object] = [[], None, "not a list"]
    for empty in empties:
        result = _run(empty)
        assert result["results"] == [] and result["range"] is None
        assert result["stacks_given"] == 0 and "no stack was given" in result["warnings"][0]


def test_a_non_dict_entry_is_an_unusable_stack() -> None:
    result = _run([_stack(), "junk"])
    assert result["results"][1]["max_concentration"] is None
    assert result["stacks_evaluated"] == 1


def test_no_iur_nulls_only_the_cancer_risk_range() -> None:
    result = _run([_stack(), _stack(50.0)], tox=Toxicity(rfc=0.01, iur=None))
    assert _range(result)["cancer_risk"] is None
    assert _range(result)["hq"] is not None
    assert _range(result)["max_concentration"] is not None


def test_doubled_emission_doubles_every_concentration() -> None:
    once, twice = _run([_stack(), _stack(50.0)]), _run([_stack(), _stack(50.0)], q=2 * Q)
    for a, b in zip(once["results"], twice["results"], strict=True):
        assert math.isclose(2 * a["max_concentration"], b["max_concentration"])  # type: ignore[operator]


def test_nothing_evaluable_gives_a_null_range() -> None:
    result = _run([_stack(temperature=None)])
    assert result["range"] is None and result["stacks_evaluated"] == 0
