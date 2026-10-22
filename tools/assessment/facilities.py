"""Batch facility assessment tool: the whole exposure chain for every listed facility, in code."""

from __future__ import annotations

import copy
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace

from langchain_core.tools import tool

from commons.cas import format_cas
from config.assessment import AssessmentSettings, get_assessment_settings
from tools.assessment.helpers.chain import assess_all, refine_all, worst_case_only
from tools.assessment.helpers.screening import can_screen, unit_bound
from tools.assessment.helpers.steps import Steps
from tools.assessment.helpers.tiers import Screen, Split, screen, split
from tools.assessment.helpers.view import Findings, assessment_view
from tools.emissions.industry import fetch_facility_industry
from tools.emissions.inventory import inventory_listing, with_eis_ids
from tools.emissions.process import lookup_scc_process_description
from tools.emissions.stack import fetch_stack_parameters_from_nei, fetch_stack_parameters_from_scc
from tools.exposure.meteorology import get_meteorological_boundary
from tools.exposure.metrics import calculate_exposure_metrics
from tools.exposure.population import get_population_receptors
from tools.informatics.properties import fetch_chemical_properties
from tools.schemas import (
    AssessmentArtifact,
    AssessmentResult,
    EmissionRecord,
    FacilityExposure,
    Meteorology,
    NeiStackResult,
    NotAssessed,
    Population,
    SccLookupResult,
    StackParameters,
    Toxicity,
)

logger = logging.getLogger(__name__)
Outcome = tuple[AssessmentResult, AssessmentArtifact]
# The SCC index (a Chroma store opened on first use) is not safe to open or search from
# several threads at once, so the facilities take turns for that one step.
_SCC_LOCK = threading.Lock()


def _scc(title: str) -> SccLookupResult:
    with _SCC_LOCK:
        return lookup_scc_process_description.invoke({"naics_description": title})


def _nei(frs_id: str, eis_ids: list[str]) -> NeiStackResult:
    return fetch_stack_parameters_from_nei.invoke({"frs_id": frs_id, "eis_ids": eis_ids})


def _weather(latitude: float, longitude: float, year: int | None) -> Meteorology:
    args = {"latitude": latitude, "longitude": longitude, "reporting_year": year}
    return get_meteorological_boundary.invoke(args)


def _people(latitude: float, longitude: float, radius_km: float | None) -> Population:
    args = {"latitude": latitude, "longitude": longitude, "radius_km": radius_km}
    return get_population_receptors.invoke(args)


def _exposure(
    rate: float,
    stacks: list[StackParameters],
    weather: Meteorology,
    people: Population,
    toxicity: Toxicity,
) -> FacilityExposure:
    args = {
        "emission_rate": rate,
        "stacks": stacks,
        "meteorology": weather,
        "population": people,
        "toxicity": toxicity,
    }
    return calculate_exposure_metrics.invoke(args)


def default_steps() -> Steps:
    """Each step is the single tool it stands for (the edge where they are wired)."""
    return Steps(
        nei=_nei,
        industry=lambda doc: fetch_facility_industry.invoke({"doc_ctrl_num": doc}),
        scc=_scc,
        pstk=lambda scc: fetch_stack_parameters_from_scc.invoke({"scc_code": scc}),
        weather=_weather,
        people=_people,
        exposure=_exposure,
    )


def _toxicity(cas: str, given: Toxicity | None) -> tuple[Toxicity, str, list[str]]:
    """The benchmarks passed in, else the chemical's own from CompTox.

    Only the benchmark warnings are kept, unless both benchmarks are missing: then every
    warning is kept, since one of them may say why (CompTox unreachable, CAS not found).
    """
    if given is not None:
        return Toxicity(rfc=given.get("rfc"), iur=given.get("iur")), "given", []
    found = fetch_chemical_properties.invoke({"cas_number": cas})
    warnings = list(found["warnings"])
    if found["rfc"] is not None or found["iur"] is not None:  # else every warning may say why
        warnings = [w for w in warnings if "rfc" in w.lower() or "iur" in w.lower()]
    return Toxicity(rfc=found["rfc"], iur=found["iur"]), "CompTox", warnings


def _once_per_title(scc: Callable[[str], SccLookupResult]) -> Callable[[str], SccLookupResult]:
    """The SCC search, made once per industry title in a call (facilities share titles)."""
    found: dict[str, SccLookupResult] = {}
    lock = threading.Lock()

    def lookup(title: str) -> SccLookupResult:
        with lock:
            if title not in found:
                found[title] = scc(title)
            return copy.deepcopy(found[title])

    return lookup


def _chosen(
    records: list[EmissionRecord], frs_ids: list[str], settings: AssessmentSettings
) -> tuple[list[EmissionRecord], list[NotAssessed]]:
    """The facilities asked for, up to ``max_facilities``; those not found or over the cap."""
    wanted = list(dict.fromkeys(i.strip() for i in frs_ids if i.strip()))
    by_id = {r["frs_id"]: r for r in records}
    skipped = [
        NotAssessed(frs_id=i, reason="not in the inventory of this chemical (and place)")
        for i in wanted
        if i not in by_id
    ]
    found = [by_id[i] for i in wanted if i in by_id]
    cap = settings.max_facilities
    skipped += [
        NotAssessed(frs_id=r["frs_id"], reason=f"only {cap} facilities are assessed per call")
        for r in found[cap:]
    ]
    return found[:cap], skipped


def _resolved(records: list[EmissionRecord]) -> list[EmissionRecord]:
    """The records, with EIS IDs looked up for any that were never looked up (beyond the list)."""
    unresolved = [r for r in records if not r["eis_ids"] and r["eis_note"] is None]
    if not unresolved:
        return records
    found = {r["frs_id"]: r for r in with_eis_ids(unresolved)}
    return [found.get(r["frs_id"], r) for r in records]


@dataclass(frozen=True)
class _Call:
    """What every path of one call shares."""

    cas: str
    records: list[EmissionRecord]
    toxicity: Toxicity
    source: str
    warnings: list[str]
    radius_km: float | None
    steps: Steps
    settings: AssessmentSettings


def _by_id(call: _Call, frs_ids: list[str]) -> Findings:
    """The facilities asked for, fully assessed without screening."""
    chosen, skipped = _chosen(call.records, frs_ids, call.settings)
    candidates = [(r, None) for r in _resolved(chosen)]
    refined = refine_all(candidates, call.toxicity, call.steps, call.settings)
    full = assess_all(refined, call.toxicity, call.radius_km, call.steps, call.settings)
    tox = (call.toxicity, call.source)
    return Findings(
        call.cas, tox, len(call.records), full, [], [], None, True, skipped, call.warnings
    )


def _refined(call: _Call, first: Screen, possible: bool) -> Split:
    """Tier 2: the candidates' own stacks and worst case, then who goes on to the full chain."""
    resolved = _resolved([record for record, _ in first.candidates])
    candidates = [(r, bound) for r, (_, bound) in zip(resolved, first.candidates, strict=True)]
    refined = refine_all(candidates, call.toxicity, call.steps, call.settings)
    return split(refined, possible, call.settings)


def _found(call: _Call, possible: bool, first: Screen, tiers: Split) -> Findings:
    """Tier 3 and the record of it all: the full chain for the riskiest, the rest kept."""
    s = call.settings
    full = assess_all(tiers.full, call.toxicity, call.radius_km, call.steps, s)
    return Findings(
        cas=call.cas,
        toxicity=(call.toxicity, call.source),
        found=len(call.records),
        full=full,
        worst_only=[worst_case_only(item, call.radius_km) for item in tiers.worst_only],
        screened_out=[*first.screened_out, *tiers.screened_out],
        thresholds=s.screening,
        possible=possible,
        skipped=first.over,
        warnings=call.warnings,
    )


def _screened(call: _Call) -> Findings:
    """Every facility screened; the ones that may matter refined, the riskiest assessed."""
    s = call.settings
    unit = unit_bound(call.steps, call.toxicity, s.screening.ambient_temperatures_k)
    possible = can_screen(unit)
    first = screen(call.records, unit if possible else None, s)
    return _found(call, possible, first, _refined(call, first, possible))


def _artifact(f: Findings) -> AssessmentArtifact:
    return AssessmentArtifact(assessed=[*f.full, *f.worst_only], screened_out=list(f.screened_out))


def run_assessment(
    cas_number: str,
    frs_ids: list[str] | None,
    place: tuple[str | None, str | None],
    radius_km: float | None,
    toxicity: Toxicity | None,
    steps: Steps,
) -> Outcome:
    """Screen (or select) the facilities, get the benchmarks, run the tiers, build both views."""
    settings = get_assessment_settings()
    cas = format_cas(cas_number)
    if cas is None:
        warning = f"{cas_number!r} is not a valid CAS registry number; nothing was assessed"
        empty = (Toxicity(rfc=None, iur=None), "none")
        f = Findings(None, empty, 0, [], [], [], None, True, [], [warning])
        view = assessment_view(f, settings.max_worst_case_listed, settings.max_screened_out_listed)
        return view, _artifact(f)
    _, records = inventory_listing(cas, *place)
    tox, source, warnings = _toxicity(cas, toxicity)
    steps = replace(steps, scc=_once_per_title(steps.scc))
    call = _Call(cas, records, tox, source, warnings, radius_km, steps, settings)
    findings = _by_id(call, frs_ids) if frs_ids else _screened(call)
    listed = (settings.max_worst_case_listed, settings.max_screened_out_listed)
    return assessment_view(findings, *listed), _artifact(findings)


@tool(response_format="content_and_artifact")
def assess_facilities(
    cas_number: str,
    frs_ids: list[str] | None = None,
    state: str | None = None,
    city: str | None = None,
    radius_km: float | None = None,
    toxicity: Toxicity | None = None,
) -> Outcome:
    """Screen every facility of a chemical and assess those that may matter, in one call.

    Purpose:
        Use this to assess the facilities of a chemical. It covers every facility of the
        chemical's inventory (for `state`/`city`), not only the largest emitters, in three
        tiers:
        (1) a conservative bound for each one (a generic short, cold stack, worst-case weather,
        a person at the maximum); a facility whose bound is below both thresholds (in
        `screening`) cannot reach a level of concern and is screened out; (2) the others get
        their own stacks and their worst case; those still below are screened out too;
        (3) the highest worst-case risks get the weather at the site, the residents and the
        representative case (`facilities`); the rest keep their own-stack worst case
        (`worst_case_only`). Call it once the chemical's CAS number is known (the inventory
        need not be listed first). Give `frs_ids` only when the user asks about particular
        facilities: they are then fully assessed without screening. Each facility's result
        already includes its stacks, the weather at its site and the residents around it.
        Report every facility in `facilities` in the results table and every one in
        `worst_case_only` (as worst case only), not a sample or a "top N", never offer the
        rest "on request", and state the screening counts, thresholds and `note`.
        Stacks follow the order of evidence, and each facility says which was used in
        `stack_tier`: "NEI" (the facility's own stacks, every candidate evaluated as a range),
        "PSTK" (process-typical stacks of the SCC processes matching the facility's industry,
        `sccs`, evaluated as a range), or "AirToxScreen global default" (a generic short, cold
        stack, used when neither exists: results can be far higher than for the real stack;
        say so).

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "110-54-3". Never a number
            recalled from a chemical's name.
        frs_ids: FRS IDs of particular facilities to assess (from the inventory); omit to
            screen every facility.
        state: Postal abbreviation, as for the inventory; omit for the whole country.
        city: City name, as for the inventory.
        radius_km: Radius to count residents in, km; omit for the default (1 mile).
        toxicity: `rfc` (mg/m3) and `iur` ((ug/m3)^-1) to use instead of the chemical's own,
            for example a read-across surrogate's values; omit to look up the chemical's.

    Returns:
        A dict with:
        - cas_number, toxicity (the rfc and iur used) and toxicity_source ("CompTox" or
          "given"); warnings say when a benchmark is missing (the matching risk is then null)
        - facilities_found: facilities in the inventory (for the place)
        - screening (null when facilities were asked for by ID): possible (false when there
          is neither an RfC nor an IUR, so nothing could be screened out), hq_threshold and
          cancer_risk_threshold (unitless), screened_out_at_bound, screened_out_with_own_stacks,
          and closest_screened_out: the screened-out facilities closest to a threshold, closest
          first (at most a few), each with frs_id, facility_name, city, state, emission_rate
          (g/s), stage ("bound" or "own stacks") and the hq and cancer_risk it was screened
          out on; when nothing was assessed, these are the results table
        - assessed: how many were fully assessed; stack_tiers: how many of them used each
          stack source
        - facilities: fully assessed, highest worst-case hazard quotient first, each with
          frs_id, facility_name, city, state, emission_rate (g/s), stack_tier,
          stacks_evaluated, sccs, industry, weather_source ("screening default" when the
          site's weather could not be read), residents and radius_km (null = 1 mile), and the
          ranges over the stacks (`low`, `high`, and the stack behind each) of concentration
          (annual average, ug/m3), hq and cancer_risk, each for the worst case and the
          representative weather (null when not computable: no benchmark, or no stack could be
          evaluated), and notes (why a better stack source could not be used, defaults, and
          the method's limits)
        - worst_case_only_count and worst_case_only: facilities still above a threshold with
          their own stacks but beyond the full-assessment cap, highest worst-case HQ first,
          each with frs_id, facility_name, city, state, emission_rate (g/s), stack_tier,
          hq_worst and cancer_risk_worst (ranges over its stacks; no weather, residents or
          representative case)
        - not_assessed: facilities asked for but not assessed, or over a cap, with the reason
        - note: what was screened out and assessed, in one sentence (report it)
        The worst case is the screening maximum between 100 m and 10 km, which may fall where
        no one lives. These are screening estimates, not regulatory determinations.
    """
    return run_assessment(cas_number, frs_ids, (state, city), radius_km, toxicity, default_steps())
