"""Guards for the project's CLAUDE.md files."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_ROOT_LINES = 80


def test_root_claude_md_stays_short() -> None:
    lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= MAX_ROOT_LINES, (
        f"CLAUDE.md has {len(lines)} lines (max {MAX_ROOT_LINES}); "
        "move detail to a folder CLAUDE.md or docs/"
    )


def test_imported_and_listed_files_exist() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("@"):
            assert (ROOT / line[1:].strip()).is_file(), line
        stripped = line.strip("- ").split(" ")[0].strip("`")
        if stripped.endswith("/CLAUDE.md"):
            assert (ROOT / stripped).is_file(), stripped
