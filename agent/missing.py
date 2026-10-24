"""Open a confirmation request when this turn's tool results report missing values.

The tools decide what is missing (their ``missing`` lists); this module only gathers those lists
from the turn's tool results, removes repeats, and writes the request. It never decides what a
result needs and never guesses a value.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from typing import cast

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage

from agent.state import AgentState
from tools.schemas import ConfirmationRequest, MissingEntry


def _this_turn(messages: Sequence[AnyMessage]) -> Sequence[AnyMessage]:
    """The messages after the last user message: the tool results of the running turn."""
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index + 1 :]
    return messages


def _is_entry(item: object) -> bool:
    return isinstance(item, dict) and isinstance(item.get("entry_id"), str)


def _entries_in(message: ToolMessage) -> list[MissingEntry]:
    """The ``missing`` entries of one tool result; none when it has no usable list."""
    if not isinstance(message.content, str):
        return []
    try:
        data: object = json.loads(message.content)
    except ValueError:
        return []
    if not isinstance(data, dict):
        return []
    raw: object = cast(dict[str, object], data).get("missing")
    if not isinstance(raw, list):
        return []
    return [cast(MissingEntry, item) for item in cast(list[object], raw) if _is_entry(item)]


def collect_missing(messages: Sequence[AnyMessage]) -> list[MissingEntry]:
    """The distinct missing entries reported by this turn's tool results, in order."""
    seen: dict[str, MissingEntry] = {}
    for message in _this_turn(messages):
        if isinstance(message, ToolMessage):
            for entry in _entries_in(message):
                seen.setdefault(entry["entry_id"], entry)
    return list(seen.values())


def open_request(entries: Sequence[MissingEntry]) -> ConfirmationRequest:
    """The request for the given entries, with a new identifier."""
    return ConfirmationRequest(request_id=uuid.uuid4().hex, entries=list(entries))


def _line(entry: MissingEntry) -> str:
    units = ", ".join(entry["accepted_units"])
    return (
        f"- {entry['quantity']} for {entry['subject']} ({entry['purpose']}). "
        f"Units: {units}; plausible range {entry['minimum']:g} to {entry['maximum']:g}."
    )


def ask_text(request: ConfirmationRequest) -> str:
    """The message that tells the user which values are missing, before the card is shown."""
    lines = [_line(entry) for entry in request["entries"]]
    return (
        "I could not find these values, and the result needs them:\n"
        + "\n".join(lines)
        + "\nYou can enter a value for each one, or proceed without it. A value that is not "
        "entered stays missing and is reported as such."
    )


def ask_for_values(state: AgentState) -> dict[str, object]:
    """The graph node that ends the turn with a request: a message and the open request."""
    request = open_request(collect_missing(state["messages"]))
    return {"messages": [AIMessage(content=ask_text(request))], "pending": request}


def route_after_tools(state: AgentState) -> str:
    """Stop and ask when the turn's tools reported missing values, otherwise keep reasoning."""
    return "ask" if collect_missing(state["messages"]) else "model"
