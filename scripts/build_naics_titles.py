"""Build the NAICS title table from the Census Bureau's six-digit code lists.

The Census Bureau publishes one workbook per NAICS vintage (``6-digit_2022_Codes.xlsx``,
``6-digit_2017_Codes.xlsx``, from https://www.census.gov/naics/), two columns: code and title.
TRI submissions carry codes of whichever vintage was current when they were filed, so the
lists are merged into one table, one row per code; where vintages disagree on a title the newest
wins, and the row says which vintage it came from. Only the standard library is used: a
workbook is a zip of XML sheets whose text cells point into a shared-strings list.

Usage: ``uv run python -m scripts.build_naics_titles [workbook ...] [-o output]``
Defaults: every ``*.xlsx`` in ``data/raw/naics`` -> ``[industry].titles_path``.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from xml.etree import ElementTree

from config.industry import get_industry_settings
from config.parsing import PROJECT_ROOT
from tools.digits import digit_string

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "naics"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
VINTAGE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
CODE_LENGTH = 6


def _shared_strings(book: zipfile.ZipFile) -> list[str]:
    """The workbook's shared-strings list, in index order (rich text joined)."""
    root = ElementTree.fromstring(book.read("xl/sharedStrings.xml"))  # noqa: S314  # trusted local file
    return ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")) for si in root]


def _cells(row: ElementTree.Element, strings: list[str]) -> list[str]:
    """The row's cell texts in column order (a shared string is resolved, a number kept)."""
    out: list[str] = []
    for cell in row.findall("m:c", NS):
        value = cell.find("m:v", NS)
        text = value.text if value is not None and value.text is not None else ""
        out.append(strings[int(text)] if cell.get("t") == "s" and text else text)
    return out


def read_workbook(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (code, title) pairs from the first sheet; rows without both are skipped."""
    with zipfile.ZipFile(path) as book:
        strings = _shared_strings(book)
        sheet = ElementTree.fromstring(book.read("xl/worksheets/sheet1.xml"))  # noqa: S314
    for row in sheet.iter(f"{{{NS['m']}}}row"):
        cells = _cells(row, strings)
        if len(cells) < 2:
            continue
        code = digit_string(cells[0])
        title = " ".join(cells[1].split())
        if code is not None and len(code) == CODE_LENGTH and title:
            yield code, title


def vintage_of(path: Path) -> int:
    """The NAICS vintage (a year) in the workbook's name."""
    found = VINTAGE.search(path.name)
    if found is None:
        raise ValueError(f"{path.name} does not name a NAICS vintage (a four-digit year)")
    return int(found.group(1))


def merge(books: Iterable[Path]) -> dict[str, tuple[str, int]]:
    """Code -> (title, vintage), the newest vintage winning; sorted by code."""
    titles: dict[str, tuple[str, int]] = {}
    for path in sorted(books, key=vintage_of):
        year = vintage_of(path)
        for code, title in read_workbook(path):
            titles[code] = (title, year)
    return dict(sorted(titles.items()))


def write_table(titles: dict[str, tuple[str, int]], output: Path) -> None:
    """Write the table as UTF-8 CSV with Unix line endings (byte-for-byte reproducible)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["naics_code", "naics_title", "vintage"])
        for code, (title, year) in titles.items():
            writer.writerow([code, title, year])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("workbooks", nargs="*", type=Path, help="Census six-digit code workbooks")
    parser.add_argument("-o", "--output", type=Path, default=get_industry_settings().titles_path)
    args = parser.parse_args(argv)
    books = args.workbooks or sorted(RAW_DIR.glob("*.xlsx"))
    if not books:
        print(f"no workbooks given and none found in {RAW_DIR}", file=sys.stderr)
        return 1
    titles = merge(books)
    write_table(titles, args.output)
    print(f"wrote {len(titles)} codes from {len(books)} workbook(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
