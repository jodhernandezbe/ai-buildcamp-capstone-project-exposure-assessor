"""Read named sheets of an xlsx workbook with the standard library (typed cell values).

A workbook is a zip of XML parts. The input is untrusted, so each member is read with a size
cap, and only the parts needed are opened: the sheet list, its relationships, the shared
strings and the requested sheets.
"""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Iterable
from xml.etree import ElementTree

from scripts.qpc.errors import QpcLayoutError

Cell = str | int | float | bool | None
Row = tuple[Cell, ...]

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
LETTERS = re.compile(r"[A-Z]+")
ALPHABET = 26


def _parse(book: zipfile.ZipFile, name: str, cap: int) -> ElementTree.Element:
    try:
        with book.open(name) as handle:
            raw = handle.read(cap + 1)
    except KeyError as error:
        raise QpcLayoutError(f"the workbook has no part {name}") from error
    if len(raw) > cap:
        raise QpcLayoutError(f"workbook part {name} is over the {cap} byte cap")
    try:
        # Untrusted input, mitigated by the download cap and the per-part cap above.
        return ElementTree.fromstring(raw)  # nosec B314  # noqa: S314
    except ElementTree.ParseError as error:
        raise QpcLayoutError(f"workbook part {name} is not valid XML") from error


def _target(path: str) -> str:
    path = path.lstrip("/")
    return path if path.startswith("xl/") else f"xl/{path}"


def sheet_paths(book: zipfile.ZipFile, cap: int) -> dict[str, str]:
    """Sheet name -> part path, from the workbook's sheet list and relationships."""
    rels = _parse(book, "xl/_rels/workbook.xml.rels", cap)
    targets = {r.get("Id"): r.get("Target") for r in rels.iter(f"{PKG}Relationship")}
    paths: dict[str, str] = {}
    for sheet in _parse(book, "xl/workbook.xml", cap).iter(f"{MAIN}sheet"):
        name, target = sheet.get("name"), targets.get(sheet.get(f"{RELS}id"))
        if name and target:
            paths[name] = _target(target)
    return paths


def _strings(book: zipfile.ZipFile, cap: int) -> list[str]:
    if "xl/sharedStrings.xml" not in book.namelist():
        return []
    root = _parse(book, "xl/sharedStrings.xml", cap)
    return ["".join(t.text or "" for t in si.iter(f"{MAIN}t")) for si in root.iter(f"{MAIN}si")]


def _column(ref: str) -> int:
    found = LETTERS.match(ref)
    if found is None:
        raise QpcLayoutError(f"cell reference {ref!r} has no column")
    return sum((ord(c) - 64) * ALPHABET**i for i, c in enumerate(reversed(found.group()))) - 1


def _number(text: str) -> int | float:
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError as error:
        raise QpcLayoutError(f"numeric cell holds {text!r}") from error


def _value(cell: ElementTree.Element, strings: list[str]) -> Cell:
    kind = cell.get("t", "n")
    if kind == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{MAIN}t"))
    node = cell.find(f"{MAIN}v")
    text = None if node is None else node.text
    if text is None:
        return None
    if kind == "s":
        return strings[int(text)]
    if kind in ("str", "e"):
        return text
    if kind == "b":
        return text == "1"
    if kind == "n":
        return _number(text)
    raise QpcLayoutError(f"unsupported cell type {kind!r}")


def _row(row: ElementTree.Element, strings: list[str]) -> Row:
    cells: dict[int, Cell] = {}
    for position, cell in enumerate(row.findall(f"{MAIN}c")):
        ref = cell.get("r")
        cells[_column(ref) if ref else position] = _value(cell, strings)
    width = max(cells, default=-1) + 1
    return tuple(cells.get(i) for i in range(width))


def read_sheets(data: bytes, names: Iterable[str], cap: int) -> dict[str, list[Row]]:
    """The rows of each named sheet; rows with no cell are dropped, blank cells are None.

    Raises:
        QpcLayoutError: If the data is not a workbook, a sheet is missing (the message lists
            the sheets present), or a part is malformed, oversized or of an unknown cell type.
    """
    wanted = tuple(names)
    try:
        book = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as error:
        raise QpcLayoutError("the download is not a valid workbook") from error
    with book:
        paths, strings = sheet_paths(book, cap), _strings(book, cap)
        missing = [name for name in wanted if name not in paths]
        if missing:
            raise QpcLayoutError(f"sheet {missing[0]!r} not found; sheets are {sorted(paths)}")
        return {
            name: [
                row
                for r in _parse(book, paths[name], cap).iter(f"{MAIN}row")
                if (row := _row(r, strings))
            ]
            for name in wanted
        }
