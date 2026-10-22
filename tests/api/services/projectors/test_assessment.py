"""The batch assessment fills the workspace like the single tools do, keyed by FRS ID."""

from __future__ import annotations

from langchain_core.messages import BaseMessage

from api.schemas.workspace import WorkspaceState
from api.services.state_serializer import build_workspace
from tests.api.services.projectors.factories import (
    RULES,
    exchange,
    exposure,
    inventory,
    record,
    stack,
    stack_result,
)

SCENARIO: dict[str, object] = {
    "max_concentration": 4.0,
    "distance_m": 500.0,
    "hq": 2.0,
    "cancer_risk": None,
}
TYPICAL: dict[str, object] = {
    "max_concentration": 1.0,
    "distance_m": 900.0,
    "hq": 0.5,
    "cancer_risk": None,
}
WEATHER: dict[str, object] = {
    "wind_speed": 3.0,
    "wind_direction": 270.0,
    "stability_class": "D",
    "ambient_temperature": 290.0,
    "source": "synthetic 2020",
    "warnings": [],
}
PEOPLE: dict[str, object] = {
    "total_population": 1000,
    "age_distribution": {"18-64": 100.0},
    "source": "synthetic ACS",
    "warnings": [],
}


def _exposure(stacks: list[dict[str, object]], hq_high: float) -> dict[str, object]:
    entry = {"low": 0.5, "high": hq_high, "low_stack": 1, "high_stack": len(stacks)}
    return {
        "results": [stack_result(i + 1, s, SCENARIO, TYPICAL) for i, s in enumerate(stacks)],
        "range": {
            "max_concentration": None,
            "hq": entry,
            "cancer_risk": None,
            "representative": {"max_concentration": None, "hq": entry, "cancer_risk": None},
        },
        "stacks_given": len(stacks),
        "stacks_evaluated": len(stacks),
        "warnings": [],
    }


def _item(
    frs_id: str, rate: float, stacks: list[dict[str, object]], **over: object
) -> dict[str, object]:
    return {
        "record": record(frs_id, rate=rate),
        "stacks": stacks,
        "stack_tier": stacks[0]["source"],
        "scc_matches": [],
        "industry": None,
        "meteorology": WEATHER,
        "population": PEOPLE,
        "radius_km": None,
        "exposure": _exposure(stacks, 2.0),
        "notes": [],
        **over,
    }


def _assessed(*items: dict[str, object]) -> list[BaseMessage]:
    return exchange(
        "assess_facilities", {"cas_number": "1-1-1"}, {"assessed": len(items)}, artifact=list(items)
    )


def _build(*parts: list[BaseMessage]) -> WorkspaceState:
    return build_workspace([m for part in parts for m in part], RULES)


def test_every_assessed_facility_gets_its_stacks_weather_residents_and_risk() -> None:
    state = _build(_assessed(_item("F1", 1.0, [stack(10.0), stack(20.0)])))
    facility = state.facilities[0]
    assert facility.frs_id == "F1" and [s.height_m for s in facility.stacks] == [10.0, 20.0]
    assert facility.status == "above"
    assert facility.meteorology is not None and facility.receptors is not None
    assert facility.receptors.radius_km == RULES.default_radius_km
    assert facility.exposure is not None and facility.exposure.hq_worst is not None
    assert state.unattributed == []


def test_facilities_with_the_same_emission_rate_keep_their_own_results() -> None:
    a = _item("A", 1.0, [stack(10.0)])
    b = _item("B", 1.0, [stack(30.0)], record={**record("B", lat=11.0, lon=-21.0, rate=1.0)})
    state = _build(_assessed(a, b))
    by_id = {f.frs_id: f for f in state.facilities}
    assert by_id["A"].stacks[0].height_m == 10.0 and by_id["B"].stacks[0].height_m == 30.0
    assert all(f.exposure is not None for f in state.facilities) and state.unattributed == []


def test_a_pstk_stack_shows_its_tier_and_scc_description() -> None:
    match = {
        "scc": "1",
        "level_one": "a",
        "level_two": "b",
        "level_three": "c",
        "level_four": "Process 1",
        "sector": "s",
        "score": 0.7,
    }
    item = _item("F1", 1.0, [stack(15.0, "PSTK", "1")], scc_matches=[match])
    shown = _build(_assessed(item)).facilities[0].stacks[0]
    assert (shown.tier, shown.scc, shown.scc_description) == (2, "1", "Process 1")


def test_a_later_single_tool_result_replaces_the_batch_one() -> None:
    later = exposure(
        1.0,
        [stack_result(1, stack(10.0), {**SCENARIO, "hq": 9.0}, TYPICAL)],
        {"low": 9.0, "high": 9.0, "low_stack": 1, "high_stack": 1},
    )
    state = _build(_assessed(_item("F1", 1.0, [stack(10.0)])), later)
    assert state.facilities[0].exposure is not None
    assert state.facilities[0].exposure.hq_worst is not None
    assert state.facilities[0].exposure.hq_worst.high == 9.0


def test_an_invalid_item_is_left_out_with_a_warning_and_no_artifact_is_skipped() -> None:
    state = _build(inventory(record("F0")), _assessed({"record": "junk"}))
    assert any("batch assessment was left out" in w for w in state.warnings)
    bare = _build(exchange("assess_facilities", {"cas_number": "1-1-1"}, {"assessed": 0}))
    assert any("carried no facility details" in w for w in bare.warnings)


def _tiered(
    assessed: list[dict[str, object]], screened_out: list[dict[str, object]]
) -> list[BaseMessage]:
    artifact = {"assessed": assessed, "screened_out": screened_out}
    return exchange(
        "assess_facilities", {"cas_number": "1-1-1"}, {"assessed": 1}, artifact=artifact
    )


def _out(frs_id: str, stage: str, hq: float, **over: object) -> dict[str, object]:
    return {
        "record": record(frs_id, lat=12.0, lon=-22.0, rate=0.01),
        "stage": stage,
        "hq": hq,
        "cancer_risk": None,
        "stacks": [],
        "stack_tier": "AirToxScreen global default",
        "reason": f"screened out ({frs_id})",
        **over,
    }


def test_a_fully_assessed_facility_says_so_with_its_bound() -> None:
    item = _item("F1", 1.0, [stack(10.0)], level="full", bound={"hq": 5.0, "cancer_risk": None})
    facility = _build(_tiered([item], [])).facilities[0]
    assert facility.screening is not None and facility.screening.outcome == "full"
    assert facility.screening.bound_hq == 5.0 and facility.screening.reason is None


def test_a_worst_case_only_facility_has_its_risk_but_no_weather_or_residents() -> None:
    item = _item(
        "F1", 1.0, [stack(10.0)], level="worst case only", meteorology=None, population=None
    )
    facility = _build(_tiered([item], [])).facilities[0]
    assert facility.screening is not None and facility.screening.outcome == "worst_case_only"
    assert facility.meteorology is None and facility.receptors is None and facility.buffer is None
    assert facility.exposure is not None and facility.status == "above"


def test_screened_out_facilities_are_placed_with_their_value_reason_and_status() -> None:
    own = _out("OWN", "own stacks", 0.02, stacks=[stack(80.0)], stack_tier="NEI")
    state = _build(_tiered([], [_out("BOUND", "bound", 0.05), own]))
    by_id = {f.frs_id: f for f in state.facilities}
    bound = by_id["BOUND"].screening
    assert bound is not None and bound.outcome == "screened_out_at_bound"
    assert (bound.bound_hq, bound.value_hq, bound.reason) == (0.05, 0.05, "screened out (BOUND)")
    assert by_id["BOUND"].stacks == [] and by_id["BOUND"].status == "below"
    with_own = by_id["OWN"].screening
    assert with_own is not None and with_own.outcome == "screened_out_with_own_stacks"
    assert with_own.bound_hq is None and with_own.value_hq == 0.02
    assert [s.height_m for s in by_id["OWN"].stacks] == [80.0]
    assert by_id["OWN"].exposure is None


def test_an_invalid_screened_out_item_is_left_out_and_a_bad_shape_is_skipped() -> None:
    state = _build(_tiered([], [{"record": "junk"}]))
    assert any("batch assessment was left out" in w for w in state.warnings)
    bad = exchange("assess_facilities", {"cas_number": "1-1-1"}, {}, artifact={"assessed": "nope"})
    assert any("carried no facility details" in w for w in _build(bad).warnings)
