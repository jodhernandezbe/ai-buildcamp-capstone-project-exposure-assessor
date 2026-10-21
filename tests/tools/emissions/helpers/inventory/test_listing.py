"""Tests for tools.emissions.helpers.inventory.listing."""

from __future__ import annotations

from tests.tools.emissions.records import emission_record
from tools.emissions.helpers.inventory.listing import rank_and_cap

RECORDS = [
    emission_record("a", 1.0),
    emission_record("b", 5.0, "LA", "Geismar"),
    emission_record("c", 3.0),
    emission_record("d", 4.0, "LA", "Baton Rouge"),
]


def test_the_largest_come_first_and_the_rest_are_cut() -> None:
    view, every = rank_and_cap(RECORDS, 2)
    assert [f["frs_id"] for f in view["facilities"]] == ["b", "d"]
    assert [f["frs_id"] for f in every] == ["b", "d", "c", "a"]
    assert (view["total_found"], view["matching"], view["shown"]) == (4, 4, 2)


def test_a_partial_list_says_so_and_how_to_see_others() -> None:
    view, _ = rank_and_cap(RECORDS, 2)
    assert view["note"] and "4" in view["note"] and "`state` or `city`" in view["note"]


def test_a_complete_list_has_no_note() -> None:
    view, _ = rank_and_cap(RECORDS, 10)
    assert view["note"] is None and view["shown"] == 4


def test_state_and_city_filters_ignore_case_and_whitespace() -> None:
    view, every = rank_and_cap(RECORDS, 10, state=" la ")
    assert [f["frs_id"] for f in view["facilities"]] == ["b", "d"]
    assert (view["total_found"], view["matching"]) == (4, 2)
    assert [f["frs_id"] for f in rank_and_cap(RECORDS, 10, city="GEISMAR")[1]] == ["b"]
    assert len(every) == 2


def test_both_filters_must_match() -> None:
    assert rank_and_cap(RECORDS, 10, state="LA", city="Houston")[0]["matching"] == 0


def test_a_blank_filter_means_no_filter() -> None:
    assert rank_and_cap(RECORDS, 10, state="  ", city="")[0]["matching"] == 4


def test_nothing_matching_says_so_only_when_a_filter_was_given() -> None:
    assert rank_and_cap(RECORDS, 10, state="ZZ")[0]["note"] == "No facility matches the filters."
    assert rank_and_cap([], 10)[0]["note"] is None


def test_a_facility_without_a_state_never_matches_a_state_filter() -> None:
    view, _ = rank_and_cap([emission_record("x", 1.0, state=None)], 10, state="TX")
    assert view["matching"] == 0


def test_the_input_is_not_changed() -> None:
    copy = list(RECORDS)
    rank_and_cap(RECORDS, 2)
    assert RECORDS == copy
