"""Section 3: every distinct source named in the workspace and what it supplied."""

from __future__ import annotations

from collections.abc import Iterator

from docx.document import Document

from api.schemas.workspace import Facility, WorkspaceState
from api.services.report.chemical import property_label
from api.services.report.document import ReportContext, empty, table

Supplied = tuple[str, str]


def _facility(facility: Facility) -> Iterator[Supplied]:
    if facility.industry and facility.industry.source:
        yield facility.industry.source, "Industry classification (NAICS)"
    if facility.operating_hours_source:
        yield facility.operating_hours_source, "Operating hours"
    for stack in facility.stacks:
        if stack.source:
            tier = f" ({stack.tier_label})" if stack.tier_label else ""
            yield stack.source, f"Stack parameters{tier}"
    if facility.receptors:
        yield facility.receptors.source, "Receptor population"
    if facility.meteorology:
        yield facility.meteorology.source, "Meteorology"


def _supplied(state: WorkspaceState) -> Iterator[Supplied]:
    for key, source in state.chemical.sources.items():
        yield source, f"Chemical property: {property_label(key)}"
    for facility in state.facilities:
        yield from _facility(facility)
    if state.receptors:
        yield state.receptors.source, "Receptor population"
    if state.meteorology:
        yield state.meteorology.source, "Meteorology"


def source_rows(state: WorkspaceState) -> list[list[str]]:
    """One row per distinct source (sorted), listing what it supplied."""
    grouped: dict[str, set[str]] = {}
    for source, what in _supplied(state):
        if source.strip():
            grouped.setdefault(source.strip(), set()).add(what)
    return [[source, "; ".join(sorted(grouped[source]))] for source in sorted(grouped)]


def write_sources(doc: Document, state: WorkspaceState, ctx: ReportContext) -> None:
    """The source table, or the empty-section sentence."""
    rows = source_rows(state)
    if not rows:
        empty(doc, ctx)
        return
    table(doc, ("Source", "Supplied"), rows)
