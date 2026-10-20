"""Scenario catalogue: query, judges, and why a scenario is blocked if it cannot run yet."""

from __future__ import annotations

from dataclasses import dataclass

from evals.scoring import Judge


@dataclass(frozen=True)
class Scenario:
    """One evaluation scenario; its cassette is ``<cassette_dir>/<id>.json``."""

    id: str
    query: str
    judges: tuple[Judge, ...] = ()
    blocked: str | None = None


_NOT_WRITTEN = "checks and cassette not written yet"

CHEMICAL_NAME_ONLY = Scenario(
    id="chemical-name-only",
    query="Run a screening exposure and risk assessment for formaldehyde air releases.",
    judges=(
        Judge(
            name="asks for CAS without inventing one",
            criteria=(
                "The text is an exposure assessor's reply to a user who named a chemical "
                "only by its common name. PASS only if the reply asks the user to provide "
                "the chemical's CAS registry number AND does not itself state a CAS number "
                "(a pattern like 50-00-0) AND does not present any facility, concentration, "
                "or risk result. Otherwise FAIL."
            ),
        ),
    ),
)

CATALOGUE: tuple[Scenario, ...] = (
    CHEMICAL_NAME_ONLY,
    Scenario("full-assessment-with-nei-stacks", "Assess CAS 96-12-8", blocked=_NOT_WRITTEN),
    Scenario("nei-empty-process-fallback", "", blocked=_NOT_WRITTEN),
    Scenario("unknown-industry-global-default", "", blocked=_NOT_WRITTEN),
    Scenario("scc-search-empty", "", blocked=_NOT_WRITTEN),
    Scenario("nationwide-many-facilities", "", blocked="needs the recursion-limit fix"),
    Scenario("null-toxicity-value", "", blocked=_NOT_WRITTEN),
    Scenario("territory-population-default", "", blocked=_NOT_WRITTEN),
    Scenario("unknown-cas", "", blocked=_NOT_WRITTEN),
    Scenario("out-of-scope-request", "", blocked=_NOT_WRITTEN),
    Scenario("tri-unreachable", "", blocked="needs the TRI-unreachable warning fix"),
    Scenario("weather-year", "", blocked="needs the meteorology year fallback fix"),
)
