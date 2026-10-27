"""Rows as Logfire returns them (strings from ``->>``, ints from counts), with synthetic figures."""

from __future__ import annotations

from collections.abc import Mapping

from api.services.monitoring.client import Project
from config.telemetry import TelemetrySettings, get_telemetry_settings

PROJECT = Project("acme", "assessor")


def settings() -> TelemetrySettings:
    return get_telemetry_settings()


def turn_row(**overrides: object) -> dict[str, object]:
    """A row of the sessions listing: one recorded turn with its call counts."""
    row: dict[str, object] = {
        "trace_id": "a" * 32,
        "start_timestamp": "2026-01-02T03:04:05.000000Z",
        "duration": 2.0,
        "sid": "s1",
        "question": "Assess benzene",
        "model": "m",
        "outcome": "ok",
        "input_tokens": "100",
        "cached_input_tokens": "40",
        "output_tokens": "20",
        "cost_usd": "0.5",
        "cost_status": "estimate",
        "model_calls": 2,
        "tool_calls": 1,
    }
    return {**row, **overrides}


def root_row(**overrides: object) -> dict[str, object]:
    """A turn span row of the detail query (no call counts; the calls are separate rows)."""
    row = turn_row(span_name=settings().spans.cli_session, status="UNSET", is_exception=False)
    for name in ("model_calls", "tool_calls"):
        row.pop(name)
    return {**row, **overrides, "op": None, "tool": None, "usage": None}


def call_row(kind: str, offset_s: int, **overrides: object) -> dict[str, object]:
    """A model (``chat``) or tool (``execute_tool``) call span row of the detail query."""
    model = kind == "chat"
    row: dict[str, object] = {
        "trace_id": "a" * 32,
        "start_timestamp": f"2026-01-02T03:04:{5 + offset_s:02d}.000000Z",
        "duration": 0.5,
        "span_name": "ChatOpenAI" if model else "fetch_thing",
        "status": "OK",
        "is_exception": False,
        "op": kind,
        "tool": None if model else "fetch_thing",
        "usage": '{"input_tokens":100,"output_tokens":20,"total_tokens":120}' if model else None,
        "sid": None,
        "model": "m-resolved" if model else None,
    }
    return {**row, **overrides}


def labels() -> Mapping[str, str]:
    return {"fetch_thing": "Fetching the thing"}
