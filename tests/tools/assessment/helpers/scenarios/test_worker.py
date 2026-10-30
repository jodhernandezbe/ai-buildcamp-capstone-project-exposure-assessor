"""Tests for the worker inhalation scenarios: the worst-case ventilation tier and its workers."""

from __future__ import annotations

import pytest

from config.occupational import get_occupational_settings
from tests.tools.assessment.helpers.scenarios.items import assessed
from tools.assessment.helpers.scenarios.worker import worker_inhalation
from tools.schemas import Toxicity, WorstCaseScenario


def _by(scenarios: list[WorstCaseScenario], quantity: str) -> WorstCaseScenario:
    return next(s for s in scenarios if s["quantity"] == quantity)


def _factor(scenario: WorstCaseScenario, key: str):  # noqa: ANN202
    return next(f for f in scenario["factors"] if f["key"] == key)


def test_the_scenario_is_the_worst_case_ventilation_tier() -> None:
    item = assessed()
    scenario = _by(worker_inhalation(item), "oel_ratio")
    tier = item["occupational_exposure"]["worst_case"]
    assert scenario["value"] == tier["oel_ratio"]
    assert _factor(scenario, "ventilation")["value"] == tier["ventilation_m3_per_s"]
    assert _factor(scenario, "mixing_factor")["value"] == tier["mixing_factor"] == 0.1
    assert scenario["tier"] == tier["risk_tier"]
    assert scenario["pathway"] == "Indoor Air → Inhalation → Worker"


def test_the_release_schedule_and_limit_are_the_factors_with_their_sources() -> None:
    scenario = _by(worker_inhalation(assessed(kg=1000.0)), "oel_ratio")
    assert _factor(scenario, "fugitive_release")["value"] == 1000.0
    assert _factor(scenario, "fugitive_release")["source"] == "TRI 2020"
    assert _factor(scenario, "shift_hours")["value"] == 16.0
    assert _factor(scenario, "shift_hours")["source"] == "test schedule"
    limit = _factor(scenario, "occupational_limit")
    assert (limit["value"], limit["source"]) == (5.0, "OSHA PEL-TWA (PubChem)")
    assert {f["group"] for f in scenario["factors"]} == {"release", "conditions", "receptor_model"}


def test_the_workers_are_the_receptors_with_the_schedule_used() -> None:
    scenario = _by(worker_inhalation(assessed()), "hq")
    (workers,) = scenario["receptors"]
    assert workers["kind"] == "workers" and workers["residents"] is None
    tenure = get_occupational_settings().tenure_years
    assert workers["note"] == f"16.0 h/day, 250.0 days/yr, {tenure:g} years of work"
    assert _factor(scenario, "worker_days_per_year")["value"] == 250.0


def test_the_benchmark_is_the_exceedance_boundary_of_the_quantity() -> None:
    limits = get_occupational_settings().thresholds
    scenarios = worker_inhalation(assessed())
    assert _by(scenarios, "oel_ratio")["benchmark"] == limits.exceedance_ratio
    assert _by(scenarios, "hq")["benchmark"] == limits.exceedance_hq
    assert _by(scenarios, "cancer_risk")["benchmark"] == limits.exceedance_cancer_risk


def test_without_a_limit_there_is_no_ratio_scenario() -> None:
    scenarios = worker_inhalation(assessed(oel=None))
    assert "oel_ratio" not in {s["quantity"] for s in scenarios}
    assert {"hq", "cancer_risk"} <= {s["quantity"] for s in scenarios}


def test_without_a_fugitive_release_there_is_no_scenario() -> None:
    item = assessed(toxicity=Toxicity(rfc=None, iur=None))
    item["occupational_exposure"] = {
        **item["occupational_exposure"],
        "worst_case": {
            **item["occupational_exposure"]["worst_case"],
            "oel_ratio": None,
            "hq": None,
            "cancer_risk": None,
        },
    }
    assert worker_inhalation(item) == []


def test_a_larger_release_gives_a_larger_ratio() -> None:
    small = _by(worker_inhalation(assessed(kg=10.0)), "oel_ratio")["value"]
    large = _by(worker_inhalation(assessed(kg=1000.0)), "oel_ratio")["value"]
    assert large == pytest.approx(small * 100.0)
