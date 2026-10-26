"""Tests for section 3 (data sources)."""

from __future__ import annotations

from api.schemas.workspace import WorkspaceState
from api.services.report.document import new_document
from api.services.report.sources import source_rows, write_sources
from tests.api.services.report.fixtures import assessed, context, facility, lines


def test_every_source_with_what_it_supplied() -> None:
    rows = dict((s, w) for s, w in source_rows(assessed()))
    assert rows["Source M"] == "Chemical property: Molecular weight"
    assert rows["Source S"] == "Stack parameters (Tier 1: Empirical NEI)"
    assert rows["Source N"] == "Industry classification (NAICS)"
    assert rows["Source H"] == "Operating hours"
    assert rows["Source P"] == "Receptor population"
    assert rows["Source W"] == "Meteorology"


def test_a_source_used_twice_is_listed_once() -> None:
    state = WorkspaceState(facilities=[facility("1"), facility("2")])
    names = [source for source, _ in source_rows(state)]
    assert names == sorted(set(names))


def test_no_source_gives_the_empty_sentence() -> None:
    doc, ctx = new_document(), context()
    write_sources(doc, WorkspaceState(), ctx)
    assert lines(doc) == [ctx.settings.empty_section]
