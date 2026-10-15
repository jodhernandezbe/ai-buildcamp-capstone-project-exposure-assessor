"""Fail when a function body is longer than the allowed number of lines.

Counted: the lines of a function body, including nested functions and multi-line
statements. Not counted: the signature, the docstring, blank lines and comment-only lines.

Usage: ``python scripts/check_function_length.py [--max N] FILE...``
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_MAX_LINES = 18


def body_line_count(node: ast.FunctionDef | ast.AsyncFunctionDef, lines: Sequence[str]) -> int:
    """Return the number of code lines in the body of ``node``.

    Args:
        node: The function definition.
        lines: The source file's lines (index 0 is line 1).

    Returns:
        Lines from the first statement after the docstring to the end of the function,
        excluding blank and comment-only lines.
    """
    body = node.body
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        if isinstance(first.value.value, str):
            body = body[1:]
    if not body:
        return 0
    end = node.end_lineno or body[-1].lineno
    window = lines[body[0].lineno - 1 : end]
    return sum(1 for text in window if text.strip() and not text.strip().startswith("#"))


def find_violations(source: str, limit: int) -> list[tuple[int, str, int]]:
    """Return ``(line, function name, body lines)`` for functions longer than ``limit``."""
    lines = source.splitlines()
    found: list[tuple[int, str, int]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            count = body_line_count(node, lines)
            if count > limit:
                found.append((node.lineno, node.name, count))
    return sorted(found)


def main(argv: Sequence[str] | None = None) -> int:
    """Check the given files; print each violation and return 1 if there were any."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=DEFAULT_MAX_LINES, dest="limit")
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)
    failed = False
    for path in args.files:
        for line, name, count in find_violations(path.read_text(encoding="utf-8"), args.limit):
            print(f"{path}:{line}: {name}() has {count} body lines (max {args.limit})")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
