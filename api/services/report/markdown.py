"""A small, safe Markdown subset written into the document (the assistant's answer).

Handles paragraphs, ``#`` headings (as bold paragraphs), bullet and numbered lists, GitHub
pipe tables, and ``**bold**``, ``*italic*`` and inline code. Anything else, raw HTML included,
is written as plain text: nothing is interpreted and nothing is dropped.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from docx.document import Document
from docx.text.paragraph import Paragraph

from api.services.report.document import table

_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
_BULLET = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMBERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_SEPARATOR = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
_INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*|_[^_\s][^_]*_)")
_CODE_FONT = "Courier New"


def _runs(paragraph: Paragraph, text: str) -> None:
    """Write ``text`` into ``paragraph`` with bold, italic and code runs."""
    for part in _INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            paragraph.add_run(part[1:-1]).font.name = _CODE_FONT
        elif part[0] in "*_" and part[-1] == part[0] and len(part) > 2:
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table(lines: Sequence[str], at: int) -> bool:
    return "|" in lines[at] and at + 1 < len(lines) and _SEPARATOR.match(lines[at + 1]) is not None


def _table(doc: Document, lines: Sequence[str], at: int) -> int:
    """Write the pipe table starting at ``at``; returns the index after it."""
    header = _cells(lines[at])
    end = at + 2
    while end < len(lines) and "|" in lines[end] and lines[end].strip():
        end += 1
    width = len(header)
    rows = [(_cells(line) + [""] * width)[:width] for line in lines[at + 2 : end]]
    table(doc, header, rows)
    return end


def _line(doc: Document, line: str) -> None:
    """Write one non-table line as a heading, list item or paragraph."""
    if match := _HEADING.match(line):
        doc.add_paragraph().add_run(match.group(1).strip()).bold = True
    elif match := _BULLET.match(line):
        _runs(doc.add_paragraph(style="List Bullet"), match.group(1))
    elif match := _NUMBERED.match(line):
        _runs(doc.add_paragraph(style="List Number"), match.group(1))
    else:
        _runs(doc.add_paragraph(), line.strip())


def write_markdown(doc: Document, text: str) -> None:
    """Write the Markdown ``text`` into the document, line by line."""
    lines = text.splitlines()
    at = 0
    while at < len(lines):
        if _is_table(lines, at):
            at = _table(doc, lines, at)
            continue
        if lines[at].strip():
            _line(doc, lines[at])
        at += 1
