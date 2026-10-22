"""Chat contract: the turn request and the server-sent events of one turn."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, RootModel

from api.schemas.base import ContractModel
from api.schemas.workspace import WorkspaceState

ThreadId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


class ChatRequest(ContractModel):
    """Body of ``POST /api/v1/chat/stream``."""

    thread_id: ThreadId
    message: str = Field(min_length=1, max_length=8000)


class _Event(ContractModel):
    seq: int = Field(ge=0, description="Position of the event in its stream, from 0.")


class TurnStarted(_Event):
    type: Literal["turn_started"] = "turn_started"
    thread_id: str
    turn_id: str


class ScopeDecision(_Event):
    type: Literal["scope"] = "scope"
    in_scope: bool


class GuardrailPivotResponse(_Event):
    """The in-character redirect sent instead of running the agent on an off-topic turn."""

    type: Literal["guardrail_pivot"] = "guardrail_pivot"
    text: str


class ToolStatus(_Event):
    """A tool step: ``started`` carries the label; ``finished`` adds the outcome."""

    type: Literal["tool_status"] = "tool_status"
    phase: Literal["started", "finished"]
    call_id: str
    tool_name: str
    label: str
    status: Literal["ok", "error"] | None = None


class WorkspaceUpdate(_Event):
    type: Literal["workspace_update"] = "workspace_update"
    state: WorkspaceState


class Token(_Event):
    type: Literal["token"] = "token"
    text: str


class AssistantMessage(_Event):
    type: Literal["assistant_message"] = "assistant_message"
    text: str


class UsageTotals(ContractModel):
    """Token counts and estimated cost (USD) of a turn or a session.

    ``cost_status`` is ``estimate`` when every call was priced, ``lower_bound`` when some call
    reported no usage, and ``unpriced`` (``cost_usd`` null) when the model has no price.
    """

    calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    complete: bool
    cost_usd: float | None
    cost_status: Literal["estimate", "lower_bound", "unpriced"]
    priced_on: str | None


class ThreadMessage(ContractModel):
    """One user or assistant message of a thread (text only, no tool calls or results)."""

    role: Literal["user", "assistant"]
    text: str


class ThreadSnapshot(ContractModel):
    """A held thread as of its last finished turn (``GET /api/v1/chat/threads/{id}``)."""

    thread_id: str
    messages: list[ThreadMessage]
    workspace: WorkspaceState
    usage: UsageTotals


class Usage(_Event):
    type: Literal["usage"] = "usage"
    turn: UsageTotals
    session: UsageTotals


class ErrorEvent(_Event):
    """A user-safe message and the id under which the details were logged."""

    type: Literal["error"] = "error"
    message: str
    correlation_id: str


class TurnFinished(_Event):
    type: Literal["turn_finished"] = "turn_finished"


StreamEvent = Annotated[
    TurnStarted
    | ScopeDecision
    | GuardrailPivotResponse
    | ToolStatus
    | WorkspaceUpdate
    | Token
    | AssistantMessage
    | Usage
    | ErrorEvent
    | TurnFinished,
    Field(discriminator="type"),
]


class StreamEventSchema(RootModel[StreamEvent]):
    """Any one event of the stream (used to export the event union)."""
