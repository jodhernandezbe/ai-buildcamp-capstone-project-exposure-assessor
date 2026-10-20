"""Replay of recorded tool outputs, so evaluation runs never hit live services.

A cassette is one JSON file per scenario: ``{tool_name: [{"args": {...}, "output": ...}]}``,
recorded from the live tools (never written by hand). A replayed tool keeps the production
name, description and argument schema, so the model sees exactly the real contract. A call
with no recording fails closed: the agent gets an error result marked ``unrecorded``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from langchain_core.tools import BaseTool, StructuredTool

UNRECORDED_KEY = "unrecorded"


def _canonical(value: object) -> object:
    if isinstance(value, Mapping):
        items = cast(Mapping[object, object], value).items()
        return {str(k): _canonical(v) for k, v in sorted(items, key=lambda kv: str(kv[0]))}
    if isinstance(value, list | tuple):
        return [_canonical(v) for v in cast(Sequence[object], value)]
    return None if value is None else str(value).strip()


def call_key(args: Mapping[str, object]) -> str:
    """Canonical key of a call's arguments (keys sorted, scalars as stripped strings)."""
    return json.dumps(_canonical(args), sort_keys=True)


@dataclass(frozen=True)
class Cassette:
    """Recorded outputs, keyed by tool name and canonical arguments."""

    outputs: Mapping[str, Mapping[str, object]] = field(
        default_factory=lambda: dict[str, Mapping[str, object]]()
    )

    @classmethod
    def load(cls, path: Path) -> Cassette:
        """Read a cassette file; a missing file is an empty cassette (every call unrecorded)."""
        if not path.is_file():
            return cls()
        raw = cast(dict[str, list[dict[str, object]]], json.loads(path.read_text()))
        return cls(
            {
                tool: {call_key(cast(Mapping[str, object], e["args"])): e["output"] for e in rows}
                for tool, rows in raw.items()
            }
        )

    def lookup(self, tool: str, args: Mapping[str, object]) -> tuple[bool, object]:
        """Return ``(found, output)`` for a call."""
        recorded = self.outputs.get(tool, {})
        key = call_key(args)
        return (key in recorded, recorded.get(key))


def _unrecorded(tool: str, args: Mapping[str, object]) -> dict[str, object]:
    return {
        "error": f"no recording for {tool}({call_key(args)}); re-record the scenario",
        UNRECORDED_KEY: True,
    }


def _clone(tool: BaseTool, func: Callable[..., object]) -> BaseTool:
    return StructuredTool.from_function(
        func=func,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,  # type: ignore[arg-type]
    )


def _replayer(tool: BaseTool, cassette: Cassette) -> Callable[..., object]:
    def replay(**kwargs: object) -> object:
        found, output = cassette.lookup(tool.name, kwargs)
        return output if found else _unrecorded(tool.name, kwargs)

    return replay


def replay_tools(
    tools: Sequence[BaseTool], cassette: Cassette, live_tools: Collection[str]
) -> list[BaseTool]:
    """Return the tools with network tools replayed from ``cassette``.

    Args:
        tools: The production tools.
        cassette: Recorded outputs.
        live_tools: Names of tools that need no network; they are returned unchanged.
    """
    return [t if t.name in live_tools else _clone(t, _replayer(t, cassette)) for t in tools]
