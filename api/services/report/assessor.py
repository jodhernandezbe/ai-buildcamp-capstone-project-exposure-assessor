"""Section 8: the assistant's last answer, labelled as model-generated."""

from __future__ import annotations

from docx.document import Document

from api.services.report.document import ReportContext, paragraph
from api.services.report.markdown import write_markdown


def write_assessor(doc: Document, answer: str | None, ctx: ReportContext) -> None:
    """The label note and the answer, or the sentence saying there is none."""
    if not answer or not answer.strip():
        paragraph(doc, ctx.settings.no_assessor_summary, italic=True)
        return
    paragraph(doc, ctx.settings.assessor_note, italic=True)
    write_markdown(doc, answer)
