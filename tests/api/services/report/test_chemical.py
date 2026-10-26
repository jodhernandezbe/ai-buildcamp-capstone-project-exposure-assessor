"""Tests for section 2 (chemical identity and properties)."""

from __future__ import annotations

from api.schemas.workspace import ReadAcross, WorkspaceState
from api.services.report.chemical import write_chemical
from api.services.report.document import new_document
from tests.api.services.report.fixtures import chemical, chemical_only, context, lines


def test_properties_with_sources() -> None:
    doc = new_document()
    write_chemical(doc, chemical_only(), context())
    text = lines(doc)
    assert "CAS number | 11-11-1 | " in text
    assert "Molecular weight | 11.5 g/mol | Source M" in text
    assert "RfC | 0.25 mg/m³ | Source R" in text


def test_absent_iur_is_not_reported_not_zero() -> None:
    doc = new_document()
    write_chemical(doc, chemical_only(), context())
    assert "IUR | not reported | " in lines(doc)


def test_read_across_outcome() -> None:
    doc = new_document()
    write_chemical(doc, chemical_only(), context())
    text = lines(doc)
    assert "Outcome | Read-across surrogate" in text
    assert "Surrogate | Surrogatium (CAS 2-22-2)" in text
    assert "Within applicability domain | Yes" in text


def test_read_across_not_evaluated() -> None:
    doc = new_document()
    state = WorkspaceState(chemical=chemical().model_copy(update={"read_across": ReadAcross()}))
    write_chemical(doc, state, context())
    assert "Read-across was not evaluated for this chemical." in lines(doc)
