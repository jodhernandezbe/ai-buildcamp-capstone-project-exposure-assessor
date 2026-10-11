"""Utilities for loading Markdown prompts from the ``prompts/`` directory."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Return the contents of ``prompts/<name>.md`` as a string.

    Args:
        name: File name without the ``.md`` extension (e.g. ``"agent_system"``).

    Raises:
        FileNotFoundError: If no such prompt exists.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if path.parent != PROMPTS_DIR or not path.is_file():
        raise FileNotFoundError(f"Prompt not found: {name!r} (looked in {PROMPTS_DIR})")
    return path.read_text(encoding="utf-8")


def list_prompts() -> list[str]:
    """Return the names of all available prompts, sorted."""
    return sorted(p.stem for p in PROMPTS_DIR.glob("*.md"))
