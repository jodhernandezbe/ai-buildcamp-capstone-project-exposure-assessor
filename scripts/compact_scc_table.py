"""Write the compact SCC table the index reads, from the raw EPA download.

The raw EPA SCC table has 28 columns and every data category (about 5 MB), more than the
repository's large-file limit. The index needs only the configured columns of the rows whose
category is in ``[scc_index].categories``, so this writes just those as a gzip-compressed CSV
(about 0.1 MB). The output is byte-for-byte reproducible (no timestamp in the gzip header).

Usage: ``uv run python -m scripts.compact_scc_table [raw_csv [output]]``
Defaults: ``data/raw/epa_scc_to_epa_emission_sector.csv`` -> ``[scc_index].source_path``.
"""

from __future__ import annotations

import csv
import gzip
import io
import sys
from collections.abc import Sequence
from pathlib import Path

from config.parsing import PROJECT_ROOT
from config.retrieval import SccIndexSettings, get_scc_index_settings

DEFAULT_RAW = "data/raw/epa_scc_to_epa_emission_sector.csv"


def compact_rows(raw: Path, settings: SccIndexSettings) -> tuple[list[str], list[list[str]]]:
    """Return the configured columns and the rows of the wanted categories.

    Raises:
        ValueError: If the raw table lacks a configured column.
        OSError: If the raw table cannot be read.
    """
    names = list(dict.fromkeys(settings.columns.values()))
    with raw.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in names if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{raw} lacks configured columns: {', '.join(missing)}")
        category = settings.columns["category"]
        rows = [
            [row.get(name) or "" for name in names]
            for row in reader
            if (row.get(category) or "").strip() in settings.categories
        ]
    return names, rows


def to_gzip(names: Sequence[str], rows: Sequence[Sequence[str]]) -> bytes:
    """Serialize as UTF-8 CSV (LF line ends) and gzip it deterministically."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(names)
    writer.writerows(rows)
    return gzip.compress(buffer.getvalue().encode("utf-8"), mtime=0)


def main(argv: Sequence[str]) -> int:
    """Compact ``argv[0]`` (or the default raw file) into ``argv[1]`` (or the configured path)."""
    settings = get_scc_index_settings()
    raw = Path(argv[0]) if argv else PROJECT_ROOT / DEFAULT_RAW
    target = Path(argv[1]) if len(argv) > 1 else settings.source_path
    try:
        names, rows = compact_rows(raw, settings)
    except (OSError, ValueError, csv.Error, UnicodeDecodeError) as exc:
        print(f"cannot compact the SCC table: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("no rows match [scc_index].categories; nothing written", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(to_gzip(names, rows))
    print(f"wrote {len(rows)} rows x {len(names)} columns to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
