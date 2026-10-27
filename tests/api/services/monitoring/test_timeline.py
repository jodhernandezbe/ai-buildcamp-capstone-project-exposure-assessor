"""Tests for a session's timeline: calls in start order with labels, tokens and links."""

from __future__ import annotations

from api.services.monitoring.timeline import build_turns, trace_url
from tests.api.services.monitoring.factories import (
    PROJECT,
    call_row,
    labels,
    root_row,
    settings,
)

SETTINGS = settings()


def test_calls_are_ordered_by_start_with_offsets_labels_and_tokens() -> None:
    rows = [
        call_row("execute_tool", 2),
        root_row(),
        call_row("chat", 1),
        call_row("chat", 4, usage=None),
    ]
    _, turns = build_turns(rows, SETTINGS, labels(), PROJECT)
    (turn,) = turns
    assert [(s.kind, s.name, s.offset_ms) for s in turn.steps] == [
        ("model", "m-resolved", 1000),
        ("tool", "Fetching the thing", 2000),
        ("model", "m-resolved", 4000),
    ]
    assert (turn.steps[0].input_tokens, turn.steps[0].output_tokens) == (100, 20)
    assert turn.steps[2].input_tokens is None  # no usage recorded: absent, not zero
    assert turn.steps[1].duration_ms == 500 and turn.duration_ms == 2000


def test_a_tool_without_a_label_shows_under_its_own_name() -> None:
    rows = [root_row(), call_row("execute_tool", 1, tool="other_tool")]
    _, turns = build_turns(rows, SETTINGS, labels(), PROJECT)
    assert turns[0].steps[0].name == "other_tool"


def test_a_failed_call_is_marked() -> None:
    rows = [
        root_row(),
        call_row("execute_tool", 1, status="ERROR"),
        call_row("chat", 2, is_exception=True),
    ]
    _, turns = build_turns(rows, SETTINGS, labels(), PROJECT)
    assert [s.outcome for s in turns[0].steps] == ["error", "error"]


def test_a_call_with_no_status_has_an_unknown_outcome() -> None:
    _, turns = build_turns([root_row(), call_row("chat", 1, status=None)], SETTINGS, labels(), None)
    assert turns[0].steps[0].outcome == "unknown"


def test_call_counts_come_from_the_trace() -> None:
    rows = [root_row(), call_row("chat", 1), call_row("chat", 2), call_row("execute_tool", 3)]
    records, _ = build_turns(rows, SETTINGS, labels(), PROJECT)
    assert (records[0].model_calls, records[0].tool_calls) == (2, 1)


def test_a_turn_with_no_calls_has_zero_not_unknown() -> None:
    records, turns = build_turns([root_row()], SETTINGS, labels(), PROJECT)
    assert (records[0].model_calls, records[0].tool_calls, turns[0].steps) == (0, 0, [])


def test_calls_of_another_trace_do_not_leak_into_a_turn() -> None:
    rows = [root_row(), call_row("chat", 1, trace_id="b" * 32)]
    _, turns = build_turns(rows, SETTINGS, labels(), PROJECT)
    assert turns[0].steps == []


def test_turns_are_oldest_first_each_with_its_own_link() -> None:
    second = root_row(trace_id="b" * 32, start_timestamp="2026-01-02T03:10:00Z")
    _, turns = build_turns([second, root_row()], SETTINGS, labels(), PROJECT)
    assert [t.trace_id for t in turns] == ["a" * 32, "b" * 32]
    assert turns[1].trace_url is not None and "b" * 32 in turns[1].trace_url


def test_the_trace_link_fills_the_template_and_encodes_the_names() -> None:
    template = "https://x.test/{organization}/{project}?trace={trace_id}"
    url = trace_url(template, PROJECT, "abc123")
    assert url == "https://x.test/acme/assessor?trace=abc123"
    odd = trace_url(template, type(PROJECT)("a b", "c/d?"), "t")
    assert odd == "https://x.test/a%20b/c%2Fd%3F?trace=t"


def test_without_a_known_project_there_is_no_link() -> None:
    assert trace_url("https://x.test/{trace_id}", None, "t") is None
    assert trace_url("https://x.test/{trace_id}", type(PROJECT)("", "p"), "t") is None
