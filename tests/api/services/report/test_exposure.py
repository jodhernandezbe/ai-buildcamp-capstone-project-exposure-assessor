"""Tests for section 5 (exposure assessment)."""

from __future__ import annotations

from api.schemas.workspace import WorkspaceState
from api.services.report.document import new_document
from api.services.report.exposure import write_exposure
from tests.api.services.report.fixtures import assessed, chemical_only, context, facility, lines


def test_stacks_weather_receptors_and_concentrations() -> None:
    doc = new_document()
    write_exposure(doc, assessed(), context())
    text = lines(doc)
    assert "Plant A (FRS 110000000001)" in text
    assert "1 | 15 m | 1.5 m | 12.5 m/s | 350 K | Tier 1: Empirical NEI | Source S" in text
    assert "Stacks evaluated | 1 of 1" in text
    assert "Worst-case maximum concentration | 7.5 µg/m³" in text
    assert "Representative maximum concentration | not reported" in text
    assert "Meteorology source | Source W (screening default)" in text
    assert "Population within the radius | 12,345" in text


def test_facility_without_stacks_or_results() -> None:
    doc = new_document()
    bare = facility().model_copy(
        update={"stacks": [], "exposure": None, "meteorology": None, "receptors": None}
    )
    write_exposure(doc, WorkspaceState(facilities=[bare]), context())
    text = lines(doc)
    assert "Stack parameters: not reported" in text
    assert "Modelled concentrations | not reported" in text
    assert "Meteorology | not reported" in text
    assert "Receptor population | not reported" in text


def test_no_facility_gives_the_empty_sentence() -> None:
    doc, ctx = new_document(), context()
    write_exposure(doc, chemical_only(), ctx)
    assert lines(doc) == [ctx.settings.empty_section]
