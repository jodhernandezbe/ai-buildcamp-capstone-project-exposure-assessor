"""Group recorded turns into sessions and total them.

A session's tokens and cost are the sums of its turns' own recorded usage. A figure that any
turn did not record makes the session's figure absent: a total is never built from a guess, and
a cost is never reported for turns that were not all priced.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

from api.schemas.monitoring import CostStatus, Outcome, SessionSummary
from api.services.monitoring.rows import TurnRecord


def _total(values: Sequence[int | None]) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if len(known) == len(values) else None


def _cost(turns: Sequence[TurnRecord]) -> tuple[float | None, CostStatus]:
    statuses = {turn.usage.cost_status for turn in turns}
    if None in statuses:
        return None, "unknown"
    if "unpriced" in statuses:
        return None, "unpriced"
    amounts = [turn.usage.cost_usd for turn in turns]
    known = [amount for amount in amounts if amount is not None]
    if len(known) != len(amounts):
        return None, "unknown"
    return sum(known), "lower_bound" if "lower_bound" in statuses else "estimate"


def _outcome(turns: Sequence[TurnRecord]) -> Outcome:
    outcomes = {turn.outcome for turn in turns}
    if "error" in outcomes:
        return "error"
    return "ok" if outcomes == {"ok"} else "unknown"


def _duration_ms(turns: Sequence[TurnRecord]) -> int | None:
    seconds = [turn.duration_s for turn in turns]
    known = [value for value in seconds if value is not None]
    return round(sum(known) * 1000) if len(known) == len(seconds) else None


def iso(moment: datetime) -> str:
    """A time as ISO 8601 in UTC."""
    return moment.astimezone(UTC).isoformat()


def summarize_session(turns: Sequence[TurnRecord]) -> SessionSummary:
    """The listing entry of one session from its turns (at least one)."""
    ordered = sorted(turns, key=lambda turn: turn.started)
    cost, status = _cost(ordered)
    return SessionSummary(
        session_id=ordered[0].session_id,
        started_at=iso(ordered[0].started),
        question=ordered[0].question,
        model=ordered[-1].model,
        turns=len(ordered),
        model_calls=_total([t.model_calls for t in ordered]),
        tool_calls=_total([t.tool_calls for t in ordered]),
        input_tokens=_total([t.usage.input_tokens for t in ordered]),
        cached_input_tokens=_total([t.usage.cached_input_tokens for t in ordered]),
        output_tokens=_total([t.usage.output_tokens for t in ordered]),
        cost_usd=cost,
        cost_status=status,
        duration_ms=_duration_ms(ordered),
        outcome=_outcome(ordered),
    )


def group_sessions(turns: Sequence[TurnRecord]) -> list[SessionSummary]:
    """One summary per session, newest first."""
    grouped: defaultdict[str, list[TurnRecord]] = defaultdict(list)
    for turn in turns:
        grouped[turn.session_id].append(turn)
    sessions = [summarize_session(group) for group in grouped.values()]
    return sorted(sessions, key=lambda session: session.started_at, reverse=True)
