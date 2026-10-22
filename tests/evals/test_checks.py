"""Tests for the deterministic checks, on hand-built records with synthetic placeholder values."""

from __future__ import annotations

from collections.abc import Mapping

from evals import checks as c
from evals.record import RunRecord, ToolCall

STACK_A = {
    "stack_height": 1.0,
    "stack_diameter": 2.0,
    "exit_velocity": 3.0,
    "exit_temperature": 4.0,
}
STACK_B = {
    "stack_height": 5.0,
    "stack_diameter": 6.0,
    "exit_velocity": 7.0,
    "exit_temperature": 8.0,
}
FACILITY = {
    "frs_id": "F1",
    "doc_ctrl_num": "D1",
    "latitude": 10.0,
    "longitude": -20.0,
    "emission_rate": 0.5,
}
AT_SITE = {"latitude": 10.0, "longitude": -20.0}


def _call(name: str, args: Mapping[str, object], output: object = None) -> ToolCall:
    return ToolCall(name, args, output, unrecorded=False)


def _record(*calls: ToolCall, report: str = "report", error: str | None = None) -> RunRecord:
    return RunRecord("s", "q", calls, report, error)


def _exposure(*stacks: Mapping[str, object], rate: float = 0.5) -> ToolCall:
    return _call(c.EXPOSURE, {"emission_rate": rate, "stacks": [dict(x) for x in stacks]})


def _full(*extra: ToolCall) -> RunRecord:
    return _record(
        _call(c.INVENTORY, {"cas_number": "1-2-3"}, [FACILITY]),
        _call(c.NEI_STACKS, {"frs_id": "F1"}, {"candidates": [STACK_A, STACK_B]}),
        _call(c.METEOROLOGY, AT_SITE),
        _call(c.POPULATION, AT_SITE),
        *extra,
    )


def _passes(check: c.Check, record: RunRecord) -> bool:
    return check.evaluate(record).passed


def test_completed() -> None:
    assert _passes(c.completed(), _record())
    assert not _passes(c.completed(), _record(report="", error="GraphRecursionError: x"))
    assert not _passes(c.completed(), _record(report="  "))


def test_no_unrecorded() -> None:
    assert _passes(c.no_unrecorded(), _record(_call("t", {})))
    result = c.no_unrecorded().evaluate(_record(ToolCall("t", {"a": 1}, {}, unrecorded=True)))
    assert not result.passed and "re-record" in result.reason


def test_called_with() -> None:
    record = _record(_call("t", {"cas_number": "1-2-3"}))
    assert _passes(c.called_with("t", cas_number="1-2-3"), record)
    assert not _passes(c.called_with("t", cas_number="9-9-9"), record)
    assert not _passes(c.called_with("other", cas_number="1-2-3"), record)


def test_not_called_and_no_tool_called() -> None:
    record = _record(_call("t", {}))
    assert _passes(c.not_called("x", "y"), record)
    assert not _passes(c.not_called("t"), record)
    assert _passes(c.no_tool_called(), _record())
    assert not _passes(c.no_tool_called(), record)


def test_site_inputs_per_assessed_facility() -> None:
    assert _passes(c.site_inputs_per_assessed_facility(), _full())
    no_weather = _record(*[x for x in _full().calls if x.name != c.METEOROLOGY])
    assert not _passes(c.site_inputs_per_assessed_facility(), no_weather)
    elsewhere = _record(
        *_full().calls[:2], _call(c.METEOROLOGY, {"latitude": 1.0, "longitude": 1.0})
    )
    assert not _passes(c.site_inputs_per_assessed_facility(), elsewhere)
    assert not _passes(c.site_inputs_per_assessed_facility(), _record())


def test_unknown_facility_fails_site_check() -> None:
    record = _record(_call(c.NEI_STACKS, {"frs_id": "F9"}, {"candidates": [STACK_A]}))
    reason = c.site_inputs_per_assessed_facility().evaluate(record).reason
    assert "did not return" in reason


def test_exposure_covers_every_candidate() -> None:
    check = c.exposure_covers_every_candidate()
    assert _passes(check, _full(_exposure(STACK_A, STACK_B)))
    assert _passes(check, _full(_exposure(STACK_B, STACK_A)))


def test_a_subset_of_candidates_fails_naming_them() -> None:
    result = c.exposure_covers_every_candidate().evaluate(_full(_exposure(STACK_A)))
    assert not result.passed and "candidates 2 of 2 not passed" in result.reason


def test_one_call_per_stack_fails() -> None:
    check = c.exposure_covers_every_candidate()
    assert not _passes(check, _full(_exposure(STACK_A), _exposure(STACK_B)))


def test_wrong_emission_rate_or_no_call_fails() -> None:
    check = c.exposure_covers_every_candidate()
    assert not _passes(check, _full(_exposure(STACK_A, STACK_B, rate=0.9)))
    assert not _passes(check, _full())


def test_no_fallback_for_facilities_with_candidates() -> None:
    check = c.no_fallback_for_facilities_with_candidates()
    assert _passes(check, _full())
    assert not _passes(check, _full(_call(c.INDUSTRY, {"doc_ctrl_num": "D1"})))
    assert not _passes(check, _full(_call(c.SCC_STACK, {})))
    assert not _passes(check, _full(_call(c.SCC_LOOKUP, {"naics_description": "x"})))


def test_fallback_allowed_when_a_facility_has_no_candidates() -> None:
    other = {**FACILITY, "frs_id": "F2", "doc_ctrl_num": "D2"}
    record = _record(
        _call(c.INVENTORY, {"cas_number": "1-2-3"}, [FACILITY, other]),
        _call(c.NEI_STACKS, {"frs_id": "F1"}, {"candidates": [STACK_A]}),
        _call(c.NEI_STACKS, {"frs_id": "F2"}, {"candidates": []}),
        _call(c.INDUSTRY, {"doc_ctrl_num": "D2"}),
        _call(c.SCC_STACK, {}),
    )
    assert _passes(c.no_fallback_for_facilities_with_candidates(), record)


def _batch(
    *facilities: Mapping[str, object],
    worst: tuple[Mapping[str, object], ...] = (),
    found: int | None = None,
    screened: int = 0,
) -> ToolCall:
    output = {
        "facilities": [dict(f) for f in facilities],
        "worst_case_only": [dict(w) for w in worst],
        "not_assessed": [],
        "facilities_found": len(facilities) + len(worst) + screened if found is None else found,
        "screening": {"screened_out_at_bound": screened, "screened_out_with_own_stacks": 0},
    }
    return _call(c.ASSESSMENT, {"cas_number": "1-2-3"}, output)


def test_the_batch_route_covers_every_facility_when_its_counts_add_up() -> None:
    check = c.every_facility_covered()
    assert _passes(check, _record(_batch({"frs_id": "F1"}, worst=({"frs_id": "F2"},), screened=5)))
    result = check.evaluate(_record(_batch({"frs_id": "F1"}, found=4)))
    assert not result.passed and "3 of 4 facilities unaccounted for" in result.reason


def test_facilities_screened_out_by_the_batch_route_are_covered_with_nothing_to_name() -> None:
    record = _record(_batch(screened=2), report="Both facilities were screened out.")
    assert _passes(c.every_facility_covered(), record)
    assert _passes(c.every_covered_facility_reported(), record)


def test_the_manual_route_covers_a_facility_through_its_exposure_call() -> None:
    check = c.every_facility_covered()
    assert _passes(check, _full(_exposure(STACK_A, STACK_B)))
    result = check.evaluate(_full())
    assert not result.passed and "not assessed: F1" in result.reason
    assert not _passes(check, _record())


def test_every_assessed_facility_must_be_named_in_the_report() -> None:
    call = _batch({"frs_id": "F1", "facility_name": "Plant One"}, worst=({"frs_id": "F2"},))
    check = c.every_covered_facility_reported()
    assert _passes(check, _record(call, report="PLANT ONE ... F2 worst case only"))
    result = check.evaluate(_record(call, report="Plant One only"))
    assert not result.passed and "F2" in result.reason
    by_hand = _record(
        _call(c.INVENTORY, {"cas_number": "1-2-3"}, [FACILITY]),
        _exposure(STACK_A, STACK_B),
        report="see F1",
    )
    assert _passes(check, by_hand)
    assert not _passes(check, _record())


def test_the_manual_site_input_check_does_not_apply_to_the_batch_route() -> None:
    assert _passes(c.site_inputs_per_assessed_facility(), _record(_batch({"frs_id": "F1"})))
