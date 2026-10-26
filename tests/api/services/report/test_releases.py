"""Tests for section 4 (releases)."""

from __future__ import annotations

from api.schemas.workspace import WorkspaceState
from api.services.report.document import new_document
from api.services.report.releases import write_releases
from tests.api.services.report.fixtures import assessed, chemical_only, context, facility, lines


def test_release_as_reported_and_rate_rounded() -> None:
    doc = new_document()
    write_releases(doc, assessed(), context())
    text = lines(doc)
    assert "110000000001 | Plant A | Town, TX | 325199 Chemicals" in text
    assert "110000000001 | 2023 | Air stack | 1234.5 lb | 0.125 g/s | 8760 h/yr (Source H)" in text


def test_conditions_of_use_or_their_note() -> None:
    doc = new_document()
    bare = facility().model_copy(update={"conditions_of_use": [], "conditions_note": "no TRI form"})
    write_releases(doc, WorkspaceState(facilities=[facility(), bare]), context())
    text = lines(doc)
    assert "Plant A (FRS 110000000001): Domestic manufacturing (Manufacturing; TRI Produce)" in text
    assert "Plant A (FRS 110000000001): no TRI form" in text


def test_no_facility_gives_the_empty_sentence() -> None:
    doc, ctx = new_document(), context()
    write_releases(doc, chemical_only(), ctx)
    assert lines(doc) == [ctx.settings.empty_section]
