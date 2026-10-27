"""Tests for totalling turns into sessions: a figure any turn lacks makes the total absent."""

from __future__ import annotations

import pytest

from api.services.monitoring.rows import TurnRecord, parse_turn
from api.services.monitoring.sessions import group_sessions, summarize_session
from tests.api.services.monitoring.factories import turn_row


def _turn(**overrides: object) -> TurnRecord:
    turn = parse_turn(turn_row(**overrides))
    assert turn is not None
    return turn


def test_a_single_run_is_a_session_of_one_turn() -> None:
    session = summarize_session([_turn()])
    assert (session.session_id, session.turns, session.question) == ("s1", 1, "Assess benzene")
    assert (session.model_calls, session.tool_calls) == (2, 1)
    assert (session.input_tokens, session.cached_input_tokens, session.output_tokens) == (
        100,
        40,
        20,
    )
    assert (session.cost_usd, session.cost_status, session.duration_ms) == (0.5, "estimate", 2000)
    assert session.outcome == "ok" and session.started_at == "2026-01-02T03:04:05+00:00"


def test_the_turns_of_a_thread_are_summed_oldest_first() -> None:
    later = _turn(start_timestamp="2026-01-02T03:10:00Z", question="And toluene?", model="m2")
    session = summarize_session([later, _turn()])
    assert (session.turns, session.question, session.model) == (2, "Assess benzene", "m2")
    assert (session.input_tokens, session.model_calls, session.tool_calls) == (200, 4, 2)
    assert (session.cost_usd, session.duration_ms) == (1.0, 4000)


def test_a_figure_one_turn_did_not_record_is_absent_not_zero() -> None:
    session = summarize_session([_turn(), _turn(input_tokens=None, duration=None)])
    assert session.input_tokens is None and session.duration_ms is None
    assert session.output_tokens == 40  # the other figures are unaffected


def test_a_cost_is_reported_only_when_every_turn_recorded_one() -> None:
    session = summarize_session([_turn(), _turn(cost_usd=None)])
    assert (session.cost_usd, session.cost_status) == (None, "unknown")


def test_a_turn_without_a_cost_status_makes_the_status_unknown() -> None:
    session = summarize_session([_turn(cost_status=None)])
    assert (session.cost_usd, session.cost_status) == (None, "unknown")


def test_an_unpriced_turn_leaves_the_session_unpriced() -> None:
    unpriced = _turn(cost_usd=None, cost_status="unpriced")
    session = summarize_session([_turn(), unpriced])
    assert (session.cost_usd, session.cost_status) == (None, "unpriced")


def test_a_lower_bound_turn_makes_the_session_a_lower_bound() -> None:
    session = summarize_session([_turn(), _turn(cost_status="lower_bound")])
    assert session.cost_status == "lower_bound" and session.cost_usd == 1.0


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [(["ok", "ok"], "ok"), (["ok", "error"], "error"), (["ok", "weird"], "unknown")],
)
def test_the_outcome_is_the_worst_of_the_turns(outcomes: list[str], expected: str) -> None:
    turns = [_turn(outcome=o, trace_id=str(i) * 32) for i, o in enumerate(outcomes)]
    assert summarize_session(turns).outcome == expected


def test_sessions_are_listed_newest_first() -> None:
    old = _turn(sid="old", start_timestamp="2026-01-01T00:00:00Z")
    new = _turn(sid="new", start_timestamp="2026-01-03T00:00:00Z")
    mid = _turn(sid="mid", start_timestamp="2026-01-02T00:00:00Z")
    assert [s.session_id for s in group_sessions([old, new, mid])] == ["new", "mid", "old"]
