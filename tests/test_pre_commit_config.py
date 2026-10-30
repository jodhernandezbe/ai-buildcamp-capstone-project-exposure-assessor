"""Guards for the pre-commit hook configuration."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK_ID = re.compile(r"^\s*-\s+id:\s*(\S+)", re.MULTILINE)


def _hook_ids(text: str) -> list[str]:
    return HOOK_ID.findall(text)


def _runs_before(ids: list[str], first: str, second: str) -> bool:
    return first in ids and second in ids and ids.index(first) < ids.index(second)


def test_trailing_comma_hook_runs_before_formatter() -> None:
    text = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert _runs_before(_hook_ids(text), "add-trailing-comma", "ruff-format")


def test_ordering_check_rejects_reverse_and_missing() -> None:
    assert not _runs_before(
        ["ruff-format", "add-trailing-comma"],
        "add-trailing-comma",
        "ruff-format",
    )
    assert not _runs_before(["ruff-format"], "add-trailing-comma", "ruff-format")
