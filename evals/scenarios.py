"""Scenario catalogue: query, deterministic checks, judges, and why a scenario is blocked."""

from __future__ import annotations

from dataclasses import dataclass

from evals import checks as c
from evals.judges import ASKS_FOR_CAS, COMPLETE_ASSESSMENT_REPORT, Judge


@dataclass(frozen=True)
class Scenario:
    """One evaluation scenario; its cassette is ``<cassette_dir>/<id>.json``."""

    id: str
    query: str
    checks: tuple[c.Check, ...] = ()
    judges: tuple[Judge, ...] = ()
    blocked: str | None = None


_NOT_WRITTEN = "checks and cassette not written yet"

CHEMICAL_NAME_ONLY = Scenario(
    id="chemical-name-only",
    query="Run a screening exposure and risk assessment for formaldehyde air releases.",
    checks=(c.completed(), c.no_tool_called()),
    judges=(ASKS_FOR_CAS,),
)

# 1,2-Dibromo-3-chloropropane: its live TRI inventory has two facilities, both with NEI stacks,
# which keeps the run and the cassette small. The checks are about the outcome, whichever
# route the agent takes (the batch assessment, or the chain by hand): every facility assessed
# and reported, and the chain done right when it is driven by hand.
FULL_ASSESSMENT_CAS = "96-12-8"

FULL_ASSESSMENT = Scenario(
    id="full-assessment-with-nei-stacks",
    query=(
        "Assess the inhalation exposure and health risk from air releases of "
        f"CAS {FULL_ASSESSMENT_CAS}."
    ),
    checks=(
        c.completed(),
        c.no_unrecorded(),
        c.called_with("fetch_chemical_properties", cas_number=FULL_ASSESSMENT_CAS),
        c.every_facility_covered(),
        c.every_covered_facility_reported(),
        c.site_inputs_per_assessed_facility(),
        c.exposure_covers_every_candidate(),
        c.no_fallback_for_facilities_with_candidates(),
    ),
    judges=(COMPLETE_ASSESSMENT_REPORT,),
)

CATALOGUE: tuple[Scenario, ...] = (
    CHEMICAL_NAME_ONLY,
    FULL_ASSESSMENT,
    Scenario("nei-empty-process-fallback", "", blocked=_NOT_WRITTEN),
    Scenario("unknown-industry-global-default", "", blocked=_NOT_WRITTEN),
    Scenario("scc-search-empty", "", blocked=_NOT_WRITTEN),
    Scenario("nationwide-many-facilities", "", blocked=_NOT_WRITTEN),
    Scenario("null-toxicity-value", "", blocked=_NOT_WRITTEN),
    Scenario("territory-population-default", "", blocked=_NOT_WRITTEN),
    Scenario("unknown-cas", "", blocked=_NOT_WRITTEN),
    Scenario("out-of-scope-request", "", blocked=_NOT_WRITTEN),
    Scenario("tri-unreachable", "", blocked="needs the TRI-unreachable warning fix"),
    Scenario("weather-year", "", blocked="needs the meteorology year fallback fix"),
)


def scenario(scenario_id: str) -> Scenario:
    """Return the catalogue scenario ``scenario_id``; raises ``KeyError`` if unknown."""
    for item in CATALOGUE:
        if item.id == scenario_id:
            return item
    raise KeyError(f"unknown scenario: {scenario_id}")
