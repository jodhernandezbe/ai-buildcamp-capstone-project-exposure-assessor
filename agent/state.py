"""Agent graph state."""

from __future__ import annotations

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from tools.schemas import ConfirmationRequest


class AgentState(TypedDict):
    """State passed between graph nodes.

    ``messages`` is append-only: nodes return new messages and ``add_messages``
    merges them into the history.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    # The open confirmation request when the turn stopped to ask for missing values; else absent.
    pending: NotRequired[ConfirmationRequest | None]
    # Facts about the thread's answers for the model this turn (instructions, not conversation).
    answers_note: NotRequired[str]
