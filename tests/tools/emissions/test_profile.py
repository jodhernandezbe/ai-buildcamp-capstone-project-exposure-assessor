"""Tests for the operational profile of an inventory record."""

from __future__ import annotations

import pytest

from config.cdr_sector import get_cdr_sector_settings
from config.plant_hours import get_plant_hours_settings
from tests.tools.emissions.records import emission_record
from tools.emissions.helpers.inventory.profile import build_profile
from tools.emissions.helpers.inventory.sector import get_sector_table
from tools.emissions.profile import operational_profile
from tools.schemas import ConditionOfUse, EmissionRecord

WEEKS = get_plant_hours_settings().days_per_year / 7


def _use(stage: str, category: str) -> ConditionOfUse:
    return {
        "tri_activity": "x",
        "tri_section": "3.2a",
        "lifecycle_stage": stage,
        "cou_category": category,
        "mapping_strength": "Direct",
    }


def _record(**over: object) -> EmissionRecord:
    return {**emission_record("F1", 1.0), **over}  # type: ignore[typeddict-item]


def test_complete_profile() -> None:
    record = _record(
        naics_code="325199",
        operating_hours_per_year=80 * WEEKS,
        operating_hours_source="Census QPC test, NAICS 3251: 80 plant hours/week",
        conditions_of_use=[_use("Processing", "Processing as a reactant")],
        lifecycle_stages=["Processing"],
    )
    profile = operational_profile(record)
    assert profile["naics_code"] == "325199"
    assert profile["life_cycle_stage"] == ["Processing"]
    assert profile["cou_category"] == ["Processing as a reactant"]
    assert profile["cdr_sector"] is not None and profile["cdr_sector"]["code"] == "IS21"
    assert profile["days_per_week"] == 7
    assert profile["annual_operating_hours"] == pytest.approx(80 * WEEKS)
    assert "Census QPC test" in profile["schedule_source"]


def test_no_activities_are_not_defaulted() -> None:
    profile = operational_profile(_record(conditions_note="TRI reported no activity"))
    assert profile["life_cycle_stage"] == [] and profile["cou_category"] == []
    assert "TRI reported no activity" in profile["warnings"]


def test_unknown_sector_leaves_the_rest_intact() -> None:
    profile = operational_profile(_record(naics_code="999999"))
    assert profile["cdr_sector"] is None
    assert profile["annual_operating_hours"] == 8760.0
    assert any("no industrial sector" in w for w in profile["warnings"])


def test_a_condition_category_appears_once() -> None:
    uses = [_use("Processing", "Same"), _use("Processing", "Same"), _use("Manufacturing", "Other")]
    assert operational_profile(_record(conditions_of_use=uses))["cou_category"] == ["Same", "Other"]


def test_impossible_hours_give_no_schedule_not_an_error() -> None:
    profile = operational_profile(_record(operating_hours_per_year=9000.0))
    assert profile["annual_operating_hours"] is None and profile["days_per_week"] is None
    assert any("no schedule" in w for w in profile["warnings"])


def test_build_profile_uses_the_given_tables() -> None:
    sector_settings = get_cdr_sector_settings()
    profile = build_profile(
        _record(naics_code="331110"),
        get_plant_hours_settings(),
        sector_settings,
        get_sector_table(sector_settings),
    )
    assert profile["cdr_sector"] is not None and profile["cdr_sector"]["code"] == "IS38"
