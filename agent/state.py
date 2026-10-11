"""Agent graph state."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed between graph nodes.

    ``messages`` is append-only: nodes return new messages and ``add_messages``
    merges them into the history.
    """

    messages: Annotated[list[AnyMessage], add_messages]
