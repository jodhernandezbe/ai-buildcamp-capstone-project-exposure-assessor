"""Tests for the report's building blocks."""

from __future__ import annotations

from datetime import datetime

from api.schemas.workspace import Chemical
from api.services.report.document import (
    chemical_label,
    facility_label,
    new_document,
    table,
    title_block,
)
from tests.api.services.report.fixtures import context, facility, lines


def test_chemical_label() -> None:
    ctx = context()
    assert (
        chemical_label(Chemical(cas_number="11-11-1", name="Testium"), ctx)
        == "Testium (CAS 11-11-1)"
    )
    assert chemical_label(Chemical(cas_number="11-11-1"), ctx) == "CAS 11-11-1"
    assert chemical_label(Chemical(), ctx) == "not reported"


def test_facility_label() -> None:
    plant = facility()
    assert facility_label(plant) == "Plant A (FRS 110000000001)"
    assert facility_label(plant.model_copy(update={"name": None})) == "FRS 110000000001"


def test_title_block_has_title_disclaimer_and_time() -> None:
    doc, ctx = new_document(), context()
    title_block(doc, ctx, Chemical(cas_number="11-11-1"), datetime(2026, 1, 2, 3, 4))
    text = lines(doc)
    assert text[0] == ctx.settings.title
    assert "Generated 2026-01-02 03:04" in text
    assert ctx.settings.disclaimer in text


def test_page_header_has_logo_and_brand() -> None:
    doc, ctx = new_document(), context()
    title_block(doc, ctx, Chemical(cas_number="11-11-1"), datetime(2026, 1, 2, 3, 4))
    header = doc.sections[0].header.paragraphs[0]
    assert ctx.settings.brand in header.text
    assert header._p.xml.count("<pic:pic") == 1  # pyright: ignore[reportPrivateUsage]
    assert len(doc.inline_shapes) == 0  # the logo is in the header, not the body


def test_page_footer_has_page_number_and_count_fields() -> None:
    doc, ctx = new_document(), context()
    title_block(doc, ctx, Chemical(), datetime(2026, 1, 2, 3, 4))
    xml = doc.sections[0].footer.paragraphs[0]._p.xml  # pyright: ignore[reportPrivateUsage]
    assert 'w:instr="PAGE"' in xml
    assert 'w:instr="NUMPAGES"' in xml
    assert xml.index('"PAGE"') < xml.index('"NUMPAGES"')
    assert "Page " in xml and " of " in xml


def test_table_has_header_and_rows() -> None:
    doc = new_document()
    table(doc, ("A", "B"), [["1", "2"], ["3", "4"]])
    assert lines(doc) == ["A | B", "1 | 2", "3 | 4"]
