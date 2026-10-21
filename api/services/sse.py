"""Server-sent-event encoding of stream events."""

from __future__ import annotations

from pydantic import BaseModel


def encode_event(event: BaseModel) -> str:
    """One SSE frame: the event as a single-line JSON ``data`` field."""
    return f"data: {event.model_dump_json()}\n\n"
