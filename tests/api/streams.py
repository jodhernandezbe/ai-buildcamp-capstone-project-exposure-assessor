"""Helpers for the streaming tests: an SSE parser (the scripted chat model is in tests/fakes.py)."""

from __future__ import annotations

import json
from typing import Any


def parse_sse(text: str) -> list[dict[str, Any]]:
    """Decode an SSE body into its JSON events."""
    frames = [frame for frame in text.split("\n\n") if frame.strip()]
    assert all(frame.startswith("data: ") for frame in frames), frames
    return [json.loads(frame.removeprefix("data: ")) for frame in frames]
