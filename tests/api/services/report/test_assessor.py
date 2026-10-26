"""Tests for section 8 (assessor summary) and its Markdown subset."""

from __future__ import annotations

from api.services.report.assessor import write_assessor
from api.services.report.document import new_document
from api.services.report.markdown import write_markdown
from tests.api.services.report.fixtures import context, lines


def test_label_note_then_answer() -> None:
    doc, ctx = new_document(), context()
    write_assessor(doc, "Plain answer.", ctx)
    assert lines(doc) == [ctx.settings.assessor_note, "Plain answer."]


def test_no_answer() -> None:
    doc, ctx = new_document(), context()
    write_assessor(doc, None, ctx)
    assert lines(doc) == [ctx.settings.no_assessor_summary]


def test_pipe_table_becomes_a_table() -> None:
    doc = new_document()
    write_markdown(doc, "Intro\n\n| A | B |\n|---|:-:|\n| 1 | 2 |\n| 3 |\n\nAfter")
    assert len(doc.tables) == 1
    assert lines(doc) == ["Intro", "A | B", "1 | 2", "3 | ", "After"]


def test_raw_html_is_text() -> None:
    doc = new_document()
    write_markdown(doc, "<script>alert(1)</script>")
    assert lines(doc) == ["<script>alert(1)</script>"]


def test_lists_headings_and_emphasis() -> None:
    doc = new_document()
    write_markdown(doc, "## Result\n- **bold** and *it* and `code`\n1. first")
    styles = [p.style.name for p in doc.paragraphs if p.style is not None]
    assert styles == ["Normal", "List Bullet", "List Number"]
    runs = doc.paragraphs[1].runs
    assert [(r.text, r.bold, r.italic) for r in runs][:3] == [
        ("bold", True, None),
        (" and ", None, None),
        ("it", None, True),
    ]
    assert lines(doc)[0] == "Result"
