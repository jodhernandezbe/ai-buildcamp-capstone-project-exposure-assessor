"""The exposure graph is the facility's own values rearranged: nodes, edges, units, reasons."""

from __future__ import annotations

from api.schemas.exposure_graph import ExposureGraph, GraphNode, GraphQuantity
from api.schemas.workspace import Facility
from api.services.exposure_graph import build_exposure_graph
from api.services.exposure_graph.parts import LaneParts, unavailable
from config.exposure_graph import GraphText
from config.ui import get_ui_settings

TEXT = get_ui_settings().exposure_graph
MISSING = TEXT.reasons["missing"]


def _tier(label: str, ratio: float | None, tier: str | None) -> dict[str, object]:
    return {
        "label": label,
        "ventilation_m3_per_s": 1.0,
        "mixing_factor": 0.5,
        "workplace_concentration_mg_m3": 2.0,
        "twa_mg_m3": 3.0,
        "oel_ratio": ratio,
        "hq": 0.2,
        "cancer_risk": None,
        "risk_tier": tier,
    }


WORKER: dict[str, object] = {
    "fugitive_release_kg_per_year": 100.0,
    "fugitive_reporting_year": 2020,
    "operating_days_per_year": 250.0,
    "hours_per_day": 8.0,
    "oel_twa_mg_m3": 5.0,
    "oel_source": "synthetic limit",
    "rfc": None,
    "iur": None,
    "vapor_pressure_mmhg": None,
    "vapor_pressure_source": None,
    "baseline": _tier("Baseline", 0.1, "acceptable"),
    "worst_case": _tier("Worst", 2.0, "exceedance"),
    "risk_tier": "acceptable",
    "assumptions": ["well mixed"],
    "warnings": [],
}


def _stack(number: int, peak: float) -> dict[str, object]:
    return {
        "stack_number": number,
        "height_m": 10.0,
        "tier": 3,
        "tier_label": "Tier 3",
        "worst_case": {"max_concentration_ug_m3": peak, "distance_m": 100.0 * number},
    }


EXPOSURE: dict[str, object] = {
    "hq_worst": {"low": 0.5, "high": 2.0, "low_stack": 1, "high_stack": 2},
    "concentration_worst": {"low": 1.0, "high": 4.0, "low_stack": 1, "high_stack": 2},
    "dose": {
        "highest_mg_kg_day": 0.3,
        "highest_band": "0-4",
        "by_band": {"0-4": 0.3, "18-64": 0.1},
    },
    "stacks_given": 2,
    "stacks_evaluated": 2,
}
PEOPLE: dict[str, object] = {
    "total_population": 1000,
    "radius_km": 2.0,
    "age_distribution": {"0-4": 10.0, "18-64": 90.0},
    "source": "synthetic census",
    "screening_default": False,
}


def _facility(**over: object) -> Facility:
    base: dict[str, object] = {
        "frs_id": "F1",
        "name": "Plant F1",
        "latitude": 1.0,
        "longitude": 2.0,
        "medium": "AIR STACK",
        "reporting_year": 2020,
        "total_release": 100.0,
        "release_unit": "Pounds",
        "emission_rate_g_s": 1.0,
        "operating_hours_per_year": 8760.0,
        "status": "above",
    }
    return Facility.model_validate({**base, **over})


def _full() -> ExposureGraph:
    return build_exposure_graph(
        _facility(
            stacks=[_stack(1, 3.0), _stack(2, 4.0)],
            exposure=EXPOSURE,
            receptors=PEOPLE,
            occupational_exposure=WORKER,
        ),
        TEXT,
    )


def _node(graph: ExposureGraph, node_id: str) -> GraphNode:
    return next(n for n in graph.nodes if n.id == node_id)


def _value(node: GraphNode, key: str) -> GraphQuantity:
    return next(q for q in node.quantities if q.key == key)


def test_each_stack_and_each_age_band_is_its_own_node() -> None:
    ids = {n.id for n in _full().nodes}
    assert {"community:stack:1", "community:stack:2"} <= ids
    assert {"community:band:0-4", "community:band:18-64"} <= ids


def test_edges_carry_the_quantities_the_tools_reported() -> None:
    edges = {e.id: e for e in _full().edges}
    stack_two = edges["community:stack:2->community:air"].quantity
    assert stack_two is not None and (stack_two.value, stack_two.unit) == (4.0, "µg/m³")
    dose = edges["community:inhale->community:band:0-4"].quantity
    assert dose is not None and (dose.value, dose.unit) == (0.3, "mg/(kg·day)")
    ratio = edges["worker:receptor->worker:endpoint"].quantity
    assert ratio is not None and (ratio.key, ratio.value) == ("oel_ratio:worst_case", 2.0)


def test_every_edge_joins_two_nodes_of_the_graph() -> None:
    graph = _full()
    ids = {n.id for n in graph.nodes}
    assert all(e.source in ids and e.target in ids for e in graph.edges)


def test_the_peak_distance_is_that_of_the_stack_with_the_peak() -> None:
    air = _node(_full(), "community:air")
    assert _value(air, "peak_distance").value == 200.0


def test_the_worker_lane_carries_both_ventilation_tiers() -> None:
    end = _node(_full(), "worker:endpoint")
    assert _value(end, "oel_ratio:worst_case").value == 2.0
    assert _value(end, "oel_ratio:baseline").value == 0.1
    assert TEXT.variants["baseline"] in _value(end, "oel_ratio:baseline").label
    assert (end.status, end.status_label) == ("above", TEXT.tiers["exceedance"])


def test_an_absent_value_carries_the_reason() -> None:
    end = _node(_full(), "worker:endpoint")
    risk = _value(end, "cancer_risk:worst_case")
    assert (risk.value, risk.reason) == (None, MISSING)


def test_a_lane_without_its_result_is_unavailable_with_the_reason() -> None:
    graph = build_exposure_graph(_facility(), TEXT)
    lanes = {lane.id: lane for lane in graph.lanes}
    assert lanes["worker"].available is False
    assert lanes["worker"].reason == TEXT.reasons["worker"]
    assert [n.id for n in graph.nodes] == ["source"]
    assert graph.edges == []


def test_without_stacks_or_bands_the_lane_still_runs_source_to_endpoint() -> None:
    graph = build_exposure_graph(_facility(exposure=EXPOSURE), TEXT)
    ids = [n.id for n in graph.nodes]
    assert "community:release" in ids and "community:residents" in ids


def test_the_annual_release_keeps_the_inventory_unit() -> None:
    total = _value(_node(_full(), "source"), "total_release")
    assert (total.value, total.unit) == (100.0, "Pounds")


def test_values_are_passed_through_unchanged() -> None:
    graph = _full()
    numbers = {q.value for n in graph.nodes for q in n.quantities if q.value is not None}
    reported = {100.0, 1.0, 8760.0, 3.0, 4.0, 10.0, 200.0, 0.3, 0.1, 90.0, 2.0}
    reported |= {1000.0, 0.5, 0.2, 5.0, 250.0, 8.0}
    assert numbers <= reported


def test_a_new_lane_is_one_builder() -> None:
    def extra(_facility: Facility, text: GraphText) -> LaneParts:
        return unavailable(text, "worker")

    graph = build_exposure_graph(_facility(), TEXT, lanes=(extra,))
    assert [lane.id for lane in graph.lanes] == ["worker"]
