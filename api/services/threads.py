"""In-memory conversation threads: history lives in the checkpointer, one turn at a time."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import InMemorySaver

from api.schemas.workspace import WorkspaceState
from api.services.usage_meter import CallUsage


class ThreadStore:
    """Holds every thread's message history (in process memory only) and who is mid-turn.

    Nothing is written to disk. ``claim`` and ``release`` are synchronous so claiming a thread
    is atomic within the event loop. With ``max_threads`` set, claiming a new thread past that
    many forgets the least recently used idle ones first; a running thread is never forgotten.
    """

    def __init__(self, max_threads: int | None = None) -> None:
        if max_threads is not None and max_threads < 1:
            raise ValueError("max_threads must be at least 1")
        self.checkpointer = InMemorySaver()
        self._max_threads = max_threads
        self._used: OrderedDict[str, None] = OrderedDict()
        self._busy: set[str] = set()
        self._usage: dict[str, list[CallUsage]] = {}
        self._tool_messages: dict[str, list[BaseMessage]] = {}
        self._workspaces: dict[str, WorkspaceState] = {}

    def claim(self, thread_id: str) -> bool:
        """Mark the thread as running a turn; False if a turn is already running."""
        if thread_id in self._busy:
            return False
        self._busy.add(thread_id)
        self.touch(thread_id)
        return True

    def touch(self, thread_id: str) -> None:
        """Mark the thread as most recently used, making room for it if it is new."""
        known = thread_id in self._used
        self._used[thread_id] = None
        self._used.move_to_end(thread_id)
        if not known:
            self._evict()

    def holds(self, thread_id: str) -> bool:
        """Whether the thread is held (it has been claimed and not forgotten)."""
        return thread_id in self._used

    def _evict(self) -> None:
        if self._max_threads is None:
            return
        for victim in [t for t in self._used if t not in self._busy]:
            if len(self._used) <= self._max_threads:
                return
            self._forget(victim)

    def messages(self, thread_id: str) -> list[BaseMessage]:
        """The thread's conversation as of its last finished step (a copy)."""
        found = self.checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
        if found is None:
            return []
        return list(found.checkpoint["channel_values"].get("messages", []))

    def release(self, thread_id: str) -> None:
        """Mark the thread idle (safe to call more than once)."""
        self._busy.discard(thread_id)

    def add_usage(self, thread_id: str, calls: Sequence[CallUsage]) -> None:
        """Add a finished turn's model calls to the thread's session usage."""
        self._usage.setdefault(thread_id, []).extend(calls)

    def session_calls(self, thread_id: str) -> list[CallUsage]:
        """Every model call of the thread so far (a copy)."""
        return list(self._usage.get(thread_id, []))

    def add_tool_messages(self, thread_id: str, messages: Sequence[BaseMessage]) -> None:
        """Keep a thread's tool calls and results, from which its workspace is rebuilt."""
        self._tool_messages.setdefault(thread_id, []).extend(messages)

    def tool_messages(self, thread_id: str) -> list[BaseMessage]:
        """The thread's tool calls and results so far (a copy)."""
        return list(self._tool_messages.get(thread_id, []))

    def workspace(self, thread_id: str) -> WorkspaceState | None:
        """The workspace last built for the thread; None before any tool result."""
        return self._workspaces.get(thread_id)

    def set_workspace(self, thread_id: str, state: WorkspaceState) -> None:
        """Remember the workspace just sent for the thread."""
        self._workspaces[thread_id] = state

    def reset(self, thread_id: str) -> bool:
        """Forget the thread's history and usage; False (nothing changed) while a turn runs."""
        if thread_id in self._busy:
            return False
        self._forget(thread_id)
        return True

    def _forget(self, thread_id: str) -> None:
        self.checkpointer.delete_thread(thread_id)
        self._used.pop(thread_id, None)
        self._usage.pop(thread_id, None)
        self._tool_messages.pop(thread_id, None)
        self._workspaces.pop(thread_id, None)
