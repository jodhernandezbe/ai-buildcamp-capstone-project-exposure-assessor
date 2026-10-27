"""Live smoke test of the Monitoring backend against the real Logfire project.

Run with ``uv run pytest -m logfire`` (needs network access and LOGFIRE_READ_TOKEN in ``.env``,
and at least one recorded run in the configured window, e.g. from ``uv run python -m app "..."``
with a write token). It reads only; nothing is written to Logfire.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from dotenv import dotenv_values

from api.schemas.monitoring import SessionsResponse
from api.services.monitoring.service import MonitoringService
from config.telemetry import get_telemetry_settings
from config.ui import get_ui_settings

pytestmark = [pytest.mark.smoke, pytest.mark.logfire, pytest.mark.anyio]
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _service() -> MonitoringService:
    """The real service, with the token read from ``.env`` (the suite hides it from the
    environment so that no other test can read it)."""
    environ = {k: v for k, v in dotenv_values(ENV_FILE).items() if v is not None}
    return MonitoringService(get_telemetry_settings(), get_ui_settings().step_labels, environ)


async def _recorded(service: MonitoringService) -> SessionsResponse:
    listing = await service.sessions()
    assert listing.state == "ok", listing.message
    if not listing.sessions:
        pytest.skip('no run was recorded in the window; run `uv run python -m app "..."` first')
    return listing


async def test_recorded_sessions_are_listed_with_their_usage_and_cost() -> None:
    session = (await _recorded(_service())).sessions[0]
    assert session.turns >= 1 and session.model_calls and session.model_calls >= 1
    assert session.input_tokens and session.input_tokens > 0
    assert session.cost_status in ("estimate", "lower_bound", "unpriced")
    assert session.outcome in ("ok", "error")


async def test_a_session_opens_with_its_calls_in_order_and_a_link_to_logfire() -> None:
    service = _service()
    summary = (await _recorded(service)).sessions[0]
    detail = await service.session(summary.session_id)
    assert detail.state == "ok" and detail.session is not None
    assert detail.session.model_calls == summary.model_calls
    steps = [step for turn in detail.turns for step in turn.steps]
    assert any(step.kind == "model" for step in steps)
    offsets = [step.offset_ms for step in detail.turns[0].steps]
    assert offsets == sorted(offsets)
    assert detail.turns[0].trace_url and detail.turns[0].trace_url.startswith("https://")
