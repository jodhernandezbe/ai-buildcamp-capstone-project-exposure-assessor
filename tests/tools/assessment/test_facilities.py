"""Tests for the assess_facilities tool: tiers, selection, benchmarks, caps and both views."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

import pytest
from langchain_core.messages import ToolMessage

from tests.tools.assessment.factories import SETTINGS, FakeSteps, match, record, stack
from tools.assessment import facilities
from tools.assessment.facilities import assess_facilities, run_assessment
from tools.emissions.helpers.inventory.listing import rank_and_cap
from tools.schemas import EmissionRecord, Toxicity

# The fake unit-rate bound is HQ 1/3 (the generic 3 m stack), so a bound reaches HQ 0.1 from
# 0.3 g/s. With its own stack the fake HQ is rate / height.
RECORDS = [
    record("BIG_TALL", emission_rate=50.0),  # bound 16.7; own 100 m stack: HQ 0.5
    record("SMALL_LOW", emission_rate=2.0),  # bound 0.67; own 1 m stack: HQ 2.0, the riskiest
    record("MID", emission_rate=10.0),  # bound 3.3; own 50 m stack: HQ 0.2
    record("TALL_ONLY", emission_rate=4.0),  # bound 1.3; own 100 m stack: HQ 0.04, out
    record("TINY", emission_rate=0.1),  # bound 0.033: out at the bound
]
HEIGHTS = {"BIG_TALL": 100.0, "SMALL_LOW": 1.0, "MID": 50.0, "TALL_ONLY": 100.0}
PROPERTIES_CALLS: list[str] = []
BENCHMARKS: dict[str, float | None] = {"rfc": 0.5, "iur": None}


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> FakeSteps:
    PROPERTIES_CALLS.clear()
    BENCHMARKS.update(rfc=0.5, iur=None)
    monkeypatch.setattr(facilities, "get_assessment_settings", lambda: SETTINGS)

    def listing(cas: str, state: str | None = None, city: str | None = None):  # noqa: ANN202
        return rank_and_cap(list(RECORDS), 2, state, city)

    class Properties:
        @staticmethod
        def invoke(args: dict[str, str]) -> dict[str, object]:
            PROPERTIES_CALLS.append(args["cas_number"])
            warnings = ["iur: not found in CompTox", "density: not found"]
            return {**BENCHMARKS, "warnings": warnings}

    monkeypatch.setattr(facilities, "inventory_listing", listing)
    monkeypatch.setattr(facilities, "fetch_chemical_properties", Properties)

    def resolved(records: list[EmissionRecord]) -> list[EmissionRecord]:
        return [{**r, "eis_ids": ["9"], "eis_note": None} for r in records]

    monkeypatch.setattr(facilities, "with_eis_ids", resolved)
    fake = FakeSteps(nei_stacks={f: [stack(h)] for f, h in HEIGHTS.items()})
    monkeypatch.setattr(facilities, "default_steps", fake.steps)
    return fake


def _run(frs_ids: list[str] | None = None, toxicity: Toxicity | None = None):  # noqa: ANN202
    return run_assessment(
        "50-00-0", frs_ids, (None, None), None, toxicity, facilities.default_steps()
    )


def _ids(items: Sequence[Mapping[str, object]]) -> list[object]:
    return [i["frs_id"] for i in items]


def test_every_facility_is_screened_and_the_riskiest_are_assessed_first(
    _offline: FakeSteps,
) -> None:
    view, artifact = _run()
    # Ranked by own-stack worst-case risk, not by emissions; the cap is 3.
    assert _ids(view["facilities"]) == ["SMALL_LOW", "BIG_TALL", "MID"]
    assert view["assessed"] == 3 and view["facilities_found"] == 5
    screening = view["screening"]
    assert screening is not None
    assert (screening["screened_out_at_bound"], screening["screened_out_with_own_stacks"]) == (1, 1)
    out = {o["record"]["frs_id"]: o["stage"] for o in artifact["screened_out"]}
    assert out == {"TINY": "bound", "TALL_ONLY": "own stacks"}
    # Nothing is requested for a facility screened out at the bound.
    assert ("nei", ("TINY", ("9",))) not in _offline.calls
    assert view["note"] is not None and "All 5 facilities were screened" in view["note"]


def test_beyond_the_full_cap_facilities_are_kept_at_their_worst_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    monkeypatch.setattr(
        facilities, "get_assessment_settings", lambda: replace(SETTINGS, max_facilities=1)
    )
    view, artifact = _run()
    assert _ids(view["facilities"]) == ["SMALL_LOW"]
    assert view["worst_case_only_count"] == 2
    assert _ids(view["worst_case_only"]) == ["BIG_TALL", "MID"]
    levels = {i["record"]["frs_id"]: i["level"] for i in artifact["assessed"]}
    assert levels == {"SMALL_LOW": "full", "BIG_TALL": "worst case only", "MID": "worst case only"}
    assert all(
        i["meteorology"] is None for i in artifact["assessed"] if i["level"] == "worst case only"
    )


def test_the_chemicals_benchmarks_are_looked_up_and_only_their_warnings_kept() -> None:
    view, _ = _run()
    assert view["toxicity"] == {"rfc": 0.5, "iur": None} and view["toxicity_source"] == "CompTox"
    assert view["warnings"] == ["iur: not found in CompTox"]
    assert PROPERTIES_CALLS == ["50-00-0"]


def test_given_benchmarks_are_used_without_a_lookup() -> None:
    given = Toxicity(rfc=2.0, iur=1e-6)
    view, _ = _run(toxicity=given)
    assert view["toxicity"] == given and view["toxicity_source"] == "given"
    assert PROPERTIES_CALLS == []


def test_without_any_benchmark_nothing_is_screened_out_and_every_warning_says_why() -> None:
    BENCHMARKS.update(rfc=None, iur=None)
    view, artifact = _run()
    assert view["warnings"] == ["iur: not found in CompTox", "density: not found"]
    assert artifact["screened_out"] == []
    assert view["screening"] is not None and not view["screening"]["possible"]
    assert view["assessed"] == 3 and view["worst_case_only_count"] == 2
    assert view["note"] is not None and "could be screened out" in view["note"]


def test_facilities_asked_for_by_id_are_assessed_without_screening(_offline: FakeSteps) -> None:
    view, artifact = _run(["TINY", " MID ", "NOPE", "TINY"])
    assert [i["record"]["frs_id"] for i in artifact["assessed"]] == ["TINY", "MID"]
    assert all(i["level"] == "full" and i["bound"] is None for i in artifact["assessed"])
    assert view["not_assessed"] == [
        {"frs_id": "NOPE", "reason": "not in the inventory of this chemical (and place)"}
    ]
    assert view["screening"] is None and artifact["screened_out"] == []


def test_facilities_asked_for_by_id_beyond_the_cap_are_reported() -> None:
    view, artifact = _run([r["frs_id"] for r in RECORDS])
    assert len(artifact["assessed"]) == 3
    assert [n["frs_id"] for n in view["not_assessed"]] == ["TALL_ONLY", "TINY"]
    assert "only 3 facilities are assessed per call" in view["not_assessed"][0]["reason"]


def test_the_scc_search_is_made_once_per_industry_title(
    monkeypatch: pytest.MonkeyPatch, _offline: FakeSteps
) -> None:
    twins = [record(f"P{i}", emission_rate=5.0, naics_title="Same Industry") for i in range(3)]

    def listing(cas: str, state: str | None = None, city: str | None = None):  # noqa: ANN202
        return rank_and_cap(twins, 2)

    monkeypatch.setattr(facilities, "inventory_listing", listing)
    _offline.matches = [match("10100101", 0.9)]
    _offline.pstk_rows = {"10100101": stack(2.0, "PSTK", "10100101")}
    view, _ = _run()
    assert sum(name == "scc" for name, _ in _offline.calls) == 1
    assert view["stack_tiers"] == {"PSTK": 3}


def test_an_invalid_cas_number_assesses_nothing() -> None:
    view, artifact = run_assessment(
        "not-a-cas", None, (None, None), None, None, facilities.default_steps()
    )
    assert artifact == {"assessed": [], "screened_out": []}
    assert view["assessed"] == 0 and "not a valid CAS" in view["warnings"][0]
    assert PROPERTIES_CALLS == []


def test_the_tool_gives_the_model_the_summary_and_the_program_every_detail() -> None:
    message = assess_facilities.invoke(
        {
            "type": "tool_call",
            "id": "c1",
            "name": "assess_facilities",
            "args": {"cas_number": "50-00-0"},
        }
    )
    assert isinstance(message, ToolMessage)
    view = json.loads(str(message.content))
    assert view["assessed"] == 3 and "facilities" in view
    assert "stacks" not in view["facilities"][0]  # the details stay out of the model's text
    assert "screened_out" not in view
    assert [i["record"]["frs_id"] for i in message.artifact["assessed"]] == [
        "SMALL_LOW",
        "BIG_TALL",
        "MID",
    ]
    assert len(message.artifact["screened_out"]) == 2


def test_schema() -> None:
    assert set(assess_facilities.args) == {
        "cas_number",
        "frs_ids",
        "state",
        "city",
        "radius_km",
        "toxicity",
    }
