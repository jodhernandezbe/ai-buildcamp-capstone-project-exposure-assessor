"""Tests for scripts.qpc.workbook."""

from __future__ import annotations

import io
import zipfile

import pytest

from scripts.qpc.errors import QpcLayoutError
from scripts.qpc.workbook import read_sheets
from tests.scripts.qpc.sheets import MAIN, workbook

CAP = 1_000_000


def test_sheet_is_found_by_name_not_position() -> None:
    data = workbook({"First": [("a",)], "Second": [("b", 2)]})
    assert read_sheets(data, ["Second"], CAP) == {"Second": [("b", 2)]}


def test_cell_types_and_blank_cells_keep_their_columns() -> None:
    data = workbook({"S": [("x", None, 3, 1.5, True)]})
    assert read_sheets(data, ["S"], CAP)["S"] == [("x", None, 3, 1.5, True)]


def test_ints_and_text_codes_stay_distinct() -> None:
    row = read_sheets(workbook({"S": [(3112, "3121")]}), ["S"], CAP)["S"][0]
    assert row == (3112, "3121") and isinstance(row[0], int)


def test_missing_sheet_lists_the_sheets_present() -> None:
    with pytest.raises(QpcLayoutError, match=r"'Gone' not found.*\['Here'\]"):
        read_sheets(workbook({"Here": [("a",)]}), ["Gone"], CAP)


def test_not_a_workbook() -> None:
    with pytest.raises(QpcLayoutError, match="not a valid workbook"):
        read_sheets(b"PK\x03\x04garbage", ["S"], CAP)


def test_part_over_the_cap_is_refused() -> None:
    with pytest.raises(QpcLayoutError, match="cap"):
        read_sheets(workbook({"S": [("a" * 500,)]}), ["S"], 300)


def _patched(name: str, xml: str) -> bytes:
    source = zipfile.ZipFile(io.BytesIO(workbook({"S": [("a",)]})))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as book:
        for item in source.namelist():
            book.writestr(item, xml if item == name else source.read(item))
    return out.getvalue()


def test_malformed_xml_is_a_layout_error() -> None:
    with pytest.raises(QpcLayoutError, match="not valid XML"):
        read_sheets(_patched("xl/worksheets/sheet1.xml", "<worksheet>"), ["S"], CAP)


def test_unknown_cell_type_is_an_error() -> None:
    cell = '<c r="A1" t="d"><v>x</v></c>'
    xml = f'<worksheet xmlns="{MAIN}"><sheetData><row r="1">{cell}</row></sheetData></worksheet>'
    with pytest.raises(QpcLayoutError, match="unsupported cell type 'd'"):
        read_sheets(_patched("xl/worksheets/sheet1.xml", xml), ["S"], CAP)


def test_inline_strings_and_error_cells() -> None:
    cells = '<c r="A1" t="inlineStr"><is><t>hi</t></is></c><c r="B1" t="e"><v>#N/A</v></c>'
    xml = f'<worksheet xmlns="{MAIN}"><sheetData><row r="1">{cells}</row></sheetData></worksheet>'
    data = _patched("xl/worksheets/sheet1.xml", xml)
    assert read_sheets(data, ["S"], CAP)["S"] == [("hi", "#N/A")]
