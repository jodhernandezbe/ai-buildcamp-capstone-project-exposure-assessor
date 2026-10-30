"""Worst-case scenarios: the combination of factors behind the high-end value of a result.

A scenario has one shape for every exposure pathway (see ``tools.schemas.WorstCaseScenario``).
Each pathway is one module that turns an assessed facility into its scenarios; ``PATHWAYS`` lists
them, so a new pathway is a new module and an entry here, with its text in ``[scenario]``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from tools.assessment.helpers.scenarios import community, worker
from tools.schemas import FacilityAssessment, ScenarioDriver, WorstCaseScenario

Builder = Callable[[FacilityAssessment], list[WorstCaseScenario]]

PATHWAYS: dict[str, Builder] = {
    community.PATHWAY: community.community_inhalation,
    worker.PATHWAY: worker.worker_inhalation,
}


def scenarios_of(item: FacilityAssessment) -> list[WorstCaseScenario]:
    """The scenarios of every registered pathway that has a value for the facility."""
    return [scenario for build in PATHWAYS.values() for scenario in build(item)]


def with_scenarios(item: FacilityAssessment) -> FacilityAssessment:
    """The facility's assessment with its scenarios."""
    return {**item, "scenarios": scenarios_of(item)}


def _stack_number(scenario: WorstCaseScenario) -> int | None:
    for item in scenario["factors"]:
        if item["key"] == "stack_number" and isinstance(item["value"], int | float):
            return int(item["value"])
    return None


def _driver(item: FacilityAssessment, scenario: WorstCaseScenario) -> ScenarioDriver:
    return ScenarioDriver(
        pathway_key=scenario["pathway_key"],
        quantity=scenario["quantity"],
        frs_id=item["record"]["frs_id"],
        facility_name=item["record"]["facility_name"],
        stack_number=_stack_number(scenario),
        value=scenario["value"],
    )


def drivers_of(items: Sequence[FacilityAssessment]) -> list[ScenarioDriver]:
    """For each pathway and quantity, the facility whose scenario has the highest value.

    The first facility wins a tie; a facility without scenarios drives nothing.
    """
    best: dict[tuple[str, str], ScenarioDriver] = {}
    for item in items:
        for scenario in item.get("scenarios", []):
            key = (scenario["pathway_key"], scenario["quantity"])
            held = best.get(key)
            if held is None or scenario["value"] > held["value"]:
                best[key] = _driver(item, scenario)
    return list(best.values())
