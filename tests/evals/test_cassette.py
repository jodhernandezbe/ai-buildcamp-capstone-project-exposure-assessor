"""Tests for cassette replay and recording (offline; no live tools)."""

from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.tools import BaseTool, tool

from evals.cassette import UNRECORDED_KEY, Cassette, Recorder, call_key, replay_tools

CALLS: list[str] = []


@tool
def network_tool(site_id: str | int) -> dict[str, object]:
    """A stand-in network tool: returns the site id it was asked for."""
    CALLS.append(str(site_id))
    return {"site": str(site_id), "values": [1, 2]}


@tool
def offline_tool(x: float) -> float:
    """A stand-in offline tool that doubles its input."""
    return 2 * x


def _replayed(cassette: Cassette) -> dict[str, BaseTool]:
    tools = replay_tools([network_tool, offline_tool], cassette, {"offline_tool"})
    return {t.name: t for t in tools}


def test_call_key_ignores_int_or_str_and_key_order() -> None:
    assert call_key({"a": 1, "b": "x "}) == call_key({"b": "x", "a": "1"})


def test_recorded_call_is_replayed_without_calling_the_tool() -> None:
    cassette = Cassette({"network_tool": {call_key({"site_id": "7"}): {"site": "seven"}}})
    CALLS.clear()
    assert _replayed(cassette)["network_tool"].invoke({"site_id": 7}) == {"site": "seven"}
    assert CALLS == []


def test_unrecorded_call_fails_closed() -> None:
    output = _replayed(Cassette())["network_tool"].invoke({"site_id": "8"})
    assert output[UNRECORDED_KEY] is True
    assert "no recording for network_tool" in output["error"]


def test_replayed_tool_keeps_the_production_contract() -> None:
    replayed = _replayed(Cassette())["network_tool"]
    assert replayed.name == network_tool.name
    assert replayed.description == network_tool.description
    assert replayed.args_schema is network_tool.args_schema


def test_live_tool_runs_for_real() -> None:
    assert _replayed(Cassette())["offline_tool"] is offline_tool


def test_missing_cassette_file_is_empty(tmp_path: Path) -> None:
    assert Cassette.load(tmp_path / "none.json").outputs == {}


def test_recording_round_trip(tmp_path: Path) -> None:
    recorder = Recorder()
    wrapped = {t.name: t for t in recorder.wrap([network_tool, offline_tool], {"offline_tool"})}
    live = wrapped["network_tool"].invoke({"site_id": "9"})
    assert wrapped["offline_tool"] is offline_tool
    path = tmp_path / "cassettes" / "scenario.json"
    recorder.save(path)
    CALLS.clear()
    assert _replayed(Cassette.load(path))["network_tool"].invoke({"site_id": 9}) == live
    assert CALLS == []


@tool
def optional_tool(site_id: str, region: str | None = None) -> dict[str, object]:
    """A stand-in tool with an optional argument."""
    return {"site": site_id, "region": region}


def _recorded_path(tmp_path: Path, recorder: Recorder) -> Path:
    path = tmp_path / "scenario.json"
    recorder.save(path)
    return path


def test_seeded_recordings_are_kept_and_new_ones_added(tmp_path: Path) -> None:
    first = Recorder()
    first_tools = first.wrap([network_tool], set())
    first.invoke(first_tools, "network_tool", {"site_id": "1"})
    path = _recorded_path(tmp_path, first)

    second = Recorder()
    second.seed(path)
    second.invoke(second.wrap([network_tool], set()), "network_tool", {"site_id": "2"})
    kept = Cassette.load(_recorded_path(tmp_path, second)).outputs["network_tool"]
    assert set(kept) == {call_key({"site_id": "1"}), call_key({"site_id": "2"})}


def test_a_new_recording_replaces_the_seeded_one_for_the_same_arguments(tmp_path: Path) -> None:
    first = Recorder()
    first.invoke(first.wrap([network_tool], set()), "network_tool", {"site_id": "1"})
    path = _recorded_path(tmp_path, first)
    second = Recorder()
    second.seed(path)
    second.invoke(second.wrap([network_tool], set()), "network_tool", {"site_id": "1"})
    rows = Cassette.load(_recorded_path(tmp_path, second)).outputs["network_tool"]
    assert len(rows) == 1


def test_seeding_from_a_missing_file_starts_empty(tmp_path: Path) -> None:
    recorder = Recorder()
    recorder.seed(tmp_path / "none.json")
    path = _recorded_path(tmp_path, recorder)
    assert Cassette.load(path).outputs == {}


def test_extra_call_key_equals_the_key_of_an_agent_call_omitting_optional_arguments(
    tmp_path: Path,
) -> None:
    recorder = Recorder()
    recorder.invoke(recorder.wrap([optional_tool], set()), "optional_tool", {"site_id": "7"})
    cassette = Cassette.load(_recorded_path(tmp_path, recorder))
    replayed = replay_tools([optional_tool], cassette, set())[0]
    assert replayed.invoke({"site_id": "7"}) == {"site": "7", "region": None}


def test_recording_an_unknown_tool_is_an_error() -> None:
    recorder = Recorder()
    with pytest.raises(KeyError, match="no tool named"):
        recorder.invoke(recorder.wrap([network_tool], set()), "missing", {})
