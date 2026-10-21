"""Deterministic checks on a ``RunRecord``: which tools were called, how often, with what.

Each factory returns a named ``Check``. Expected values (facilities, coordinates, stack
candidates, emission rates) are read from the tool outputs in the record, never written into
the check, so a check stays valid when the recordings change.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from evals.cassette import call_key
from evals.record import RunRecord, ToolCall

INVENTORY = "query_emissions_inventory"
NEI_STACKS = "fetch_stack_parameters_from_nei"
INDUSTRY = "fetch_facility_industry"
SCC_LOOKUP = "lookup_scc_process_description"
SCC_STACK = "fetch_stack_parameters_from_scc"
METEOROLOGY = "get_meteorological_boundary"
POPULATION = "get_population_receptors"
EXPOSURE = "calculate_exposure_metrics"
STACK_FIELDS = ("stack_height", "stack_diameter", "exit_velocity", "exit_temperature")
_REL_TOL = 1e-9


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one check: pass or fail, with the reason."""

    passed: bool
    reason: str


@dataclass(frozen=True)
class Check:
    """A named deterministic check."""

    name: str
    evaluate: Callable[[RunRecord], CheckResult]


Facility = Mapping[str, object]


def _verdict(problems: Sequence[str], ok: str) -> CheckResult:
    return CheckResult(False, "; ".join(problems)) if problems else CheckResult(True, ok)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def _close(a: object, b: object) -> bool:
    x, y = _number(a), _number(b)
    return x is not None and y is not None and math.isclose(x, y, rel_tol=_REL_TOL)


def _mapping(value: object) -> Facility:
    return cast(Facility, value) if isinstance(value, dict) else {}


def _dicts(value: object) -> list[Facility]:
    if isinstance(value, dict):  # the inventory's {"facilities": [...], ...} shape
        value = cast(dict[str, object], value).get("facilities")
    items = cast(list[object], value) if isinstance(value, list) else []
    return [cast(Facility, item) for item in items if isinstance(item, dict)]


def _label(call: ToolCall) -> str:
    return f"{call.name}({call_key(call.args)})"


def inventory_facilities(record: RunRecord) -> dict[str, Facility]:
    """Facilities returned by the emissions inventory, keyed by FRS ID."""
    return {
        str(f.get("frs_id")): f for call in record.calls_to(INVENTORY) for f in _dicts(call.output)
    }


def assessed_candidates(record: RunRecord) -> dict[str, list[Facility]]:
    """NEI stack candidates of each facility whose stacks the agent requested, by FRS ID."""
    found: dict[str, list[Facility]] = {}
    for call in record.calls_to(NEI_STACKS):
        found[str(call.args.get("frs_id")).strip()] = _dicts(
            _mapping(call.output).get("candidates")
        )
    return found


def completed() -> Check:
    """The run finished with a final report and no error."""

    def evaluate(record: RunRecord) -> CheckResult:
        if record.completed:
            return CheckResult(True, "run completed")
        return CheckResult(False, f"run did not finish: {record.error or 'empty report'}")

    return Check("run completed", evaluate)


def no_unrecorded() -> Check:
    """Every replayed call had a recording (else re-record the scenario)."""

    def evaluate(record: RunRecord) -> CheckResult:
        missing = [_label(c) for c in record.calls if c.unrecorded]
        problems = [f"unrecorded calls, re-record the scenario: {', '.join(missing)}"]
        return _verdict(problems if missing else [], "every call had a recording")

    return Check("no unrecorded call", evaluate)


def called_with(tool: str, **expected: object) -> Check:
    """At least one call to ``tool`` carries ``expected`` (compared as stripped strings)."""
    wanted = {k: str(v).strip() for k, v in expected.items()}

    def matches(call: ToolCall) -> bool:
        return all(str(call.args.get(k)).strip() == v for k, v in wanted.items())

    def evaluate(record: RunRecord) -> CheckResult:
        calls = record.calls_to(tool)
        if any(matches(c) for c in calls):
            return CheckResult(True, f"{tool} called with {wanted}")
        seen = ", ".join(_label(c) for c in calls) or "no call"
        return CheckResult(False, f"{tool} never called with {wanted} (seen: {seen})")

    return Check(f"{tool} called with {wanted}", evaluate)


def not_called(*tools: str) -> Check:
    """None of ``tools`` is called."""

    def evaluate(record: RunRecord) -> CheckResult:
        forbidden = [_label(c) for c in record.calls if c.name in tools]
        problems = [f"forbidden calls: {', '.join(forbidden)}"] if forbidden else []
        return _verdict(problems, f"none of {', '.join(tools)} called")

    return Check(f"not called: {', '.join(tools)}", evaluate)


def no_tool_called() -> Check:
    """The agent answered without calling any tool."""

    def evaluate(record: RunRecord) -> CheckResult:
        calls = [_label(c) for c in record.calls]
        problems = [f"tools called: {', '.join(calls)}"] if calls else []
        return _verdict(problems, "no tool called")

    return Check("no tool called", evaluate)


def _at_point(record: RunRecord, tool: str, facility: Facility) -> bool:
    return any(
        _close(c.args.get("latitude"), facility.get("latitude"))
        and _close(c.args.get("longitude"), facility.get("longitude"))
        for c in record.calls_to(tool)
    )


def _site_problems(record: RunRecord, frs_id: str, facility: Facility | None) -> list[str]:
    if facility is None:
        return [f"stacks requested for {frs_id}, which the inventory did not return"]
    return [
        f"{tool} not called at the coordinates of {frs_id}"
        for tool in (METEOROLOGY, POPULATION)
        if not _at_point(record, tool, facility)
    ]


def site_inputs_per_assessed_facility() -> Check:
    """Each facility whose stacks were requested is an inventory facility and gets weather and
    population requested at its own coordinates."""

    def evaluate(record: RunRecord) -> CheckResult:
        facilities = inventory_facilities(record)
        assessed = assessed_candidates(record)
        if not assessed:
            return CheckResult(False, "no facility had its NEI stacks requested")
        problems = [p for frs in assessed for p in _site_problems(record, frs, facilities.get(frs))]
        return _verdict(problems, f"weather and population at each of {len(assessed)} sites")

    return Check("weather and population per assessed facility", evaluate)


def _same_stack(a: Facility, b: Facility) -> bool:
    return all(_close(a.get(f), b.get(f)) for f in STACK_FIELDS)


def _carries(call: ToolCall, candidate: Facility) -> bool:
    return any(_same_stack(stack, candidate) for stack in _dicts(call.args.get("stacks")))


def _facility_calls(
    record: RunRecord, facility: Facility, candidates: list[Facility]
) -> list[ToolCall]:
    """Exposure calls for this facility: its emission rate and at least one of its stacks."""
    return [
        call
        for call in record.calls_to(EXPOSURE)
        if _close(call.args.get("emission_rate"), facility.get("emission_rate"))
        and any(_carries(call, candidate) for candidate in candidates)
    ]


def _coverage_problems(record: RunRecord, frs_id: str, facility: Facility) -> list[str]:
    candidates = assessed_candidates(record).get(frs_id, [])
    if not candidates:
        return []
    calls = _facility_calls(record, facility, candidates)
    if len(calls) != 1:
        return [f"{frs_id}: {len(calls)} exposure calls with its emission rate, expected 1"]
    missing = [str(n) for n, c in enumerate(candidates, start=1) if not _carries(calls[0], c)]
    if missing:
        return [f"{frs_id}: candidates {', '.join(missing)} of {len(candidates)} not passed"]
    return []


def exposure_covers_every_candidate() -> Check:
    """Each assessed facility with NEI candidates gets exactly one exposure call carrying every
    candidate and the facility's emission rate (candidates and rates from the record)."""

    def evaluate(record: RunRecord) -> CheckResult:
        facilities = inventory_facilities(record)
        assessed = [frs for frs in assessed_candidates(record) if frs in facilities]
        problems = [p for frs in assessed for p in _coverage_problems(record, frs, facilities[frs])]
        total = sum(len(assessed_candidates(record)[frs]) for frs in assessed)
        return _verdict(problems, f"all {total} NEI candidates passed, one call per facility")

    return Check("one exposure call per facility with every NEI candidate", evaluate)


def _with_candidates(record: RunRecord) -> tuple[set[str], bool]:
    """Control numbers of assessed facilities with NEI candidates; True if every one has some."""
    facilities = inventory_facilities(record)
    assessed = assessed_candidates(record)
    covered = {
        str(facilities[frs].get("doc_ctrl_num")).strip()
        for frs, candidates in assessed.items()
        if candidates and frs in facilities
    }
    return covered, all(assessed.values())


def no_fallback_for_facilities_with_candidates() -> Check:
    """No industry lookup for a facility that has NEI candidates, and no SCC search or SCC stack
    when every assessed facility has them."""

    def evaluate(record: RunRecord) -> CheckResult:
        covered, all_covered = _with_candidates(record)
        problems = [
            f"unneeded {_label(c)}"
            for c in record.calls_to(INDUSTRY)
            if str(c.args.get("doc_ctrl_num")).strip() in covered
        ]
        if all_covered:
            problems += [
                f"unneeded {_label(c)}" for c in record.calls if c.name in {SCC_LOOKUP, SCC_STACK}
            ]
        return _verdict(problems, "no fallback for facilities with their own stacks")

    return Check("no fallback for facilities with NEI stacks", evaluate)
