"""Tests for the prompt registry."""

from __future__ import annotations

import pytest

from prompts.registry import list_prompts, load_prompt


def test_load_prompt() -> None:
    assert "<role>" in load_prompt("agent_system")
    assert "agent_system" in list_prompts()


def test_load_prompt_missing() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("nope")
