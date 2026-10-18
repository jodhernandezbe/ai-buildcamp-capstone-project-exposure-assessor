"""Build the compact NEI stack table from the raw NEI SMOKE point flat file.

The raw file is a zip holding one 4 GB CSV (77 columns, one row per pollutant and process,
`#` comment lines first). Tier 1 needs only the distinct (EIS facility ID, stack height,
diameter, exit velocity, exit temperature) combinations, about 200,000 rows. This streams the
zip without unpacking it, drops rows whose ID is not a digit string or whose four values are not
finite and positive, and writes gzip-compressed CSV shards named by the leading digits of the ID,
each far below the repository's large-file limit. The output is sorted and byte-for-byte
reproducible (no timestamp in the gzip header).

Usage: ``uv run python -m scripts.compact_nei_stacks [raw_zip [output_dir]]``
Defaults: ``[stack.nei].raw_path`` -> ``[stack.nei].directory``.
"""

from __future__ import annotations

import csv
import io
import math
import sys
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from config.stack import STACK_QUANTITIES, NeiSettings, get_stack_settings
from scripts.compact_scc_table import to_gzip
from tools.digits import digit_string

Combinations = dict[str, set[tuple[str, ...]]]


def canonical_number(text: str) -> str | None:
    """Return a finite, positive number as canonical text (``23.0`` -> ``23``), else None."""
    try:
        value = float(text.strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return str(int(value)) if value.is_integer() else repr(value)


def _data_lines(raw: Iterable[str]) -> Iterator[str]:
    """Yield the lines that are not ``#`` comments."""
    return (line for line in raw if not line.startswith("#"))


def _positions(header: Sequence[str], nei: NeiSettings) -> tuple[int, list[int]]:
    """Return the index of the ID column and of the four value columns in the raw header."""
    wanted = [nei.raw_id_column, *(nei.raw_columns[q] for q in STACK_QUANTITIES)]
    missing = [name for name in wanted if name not in header]
    if missing:
        raise ValueError(f"raw file lacks configured columns: {', '.join(missing)}")
    indexes = [header.index(name) for name in wanted]
    return indexes[0], indexes[1:]


def _combination(row: Sequence[str], id_at: int, value_at: Sequence[int]) -> tuple[str, ...] | None:
    """Return ``(id, h, d, v, t)`` as clean text, or None if the row is unusable."""
    if len(row) <= max(id_at, *value_at):
        return None
    facility = digit_string(row[id_at])
    values = [canonical_number(row[at]) for at in value_at]
    if facility is None or any(value is None for value in values):
        return None
    return (facility, *(value for value in values if value is not None))


def read_combinations(raw_zip: Path, nei: NeiSettings) -> Combinations:
    """Stream the zip and return, per EIS ID, its distinct valid stack value combinations.

    Raises:
        ValueError: If the zip has no CSV or the raw file lacks a configured column.
        OSError, zipfile.BadZipFile, csv.Error: If the file cannot be read.
    """
    found: Combinations = defaultdict(set)
    with zipfile.ZipFile(raw_zip) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not members:
            raise ValueError(f"{raw_zip} holds no CSV file")
        with archive.open(members[0]) as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.reader(_data_lines(text))
            id_at, value_at = _positions(next(reader, None) or [], nei)
            for row in reader:
                combination = _combination(row, id_at, value_at)
                if combination is not None:
                    found[combination[0]].add(combination[1:])
    return found


def shard_rows(found: Combinations, prefix_digits: int) -> dict[str, list[list[str]]]:
    """Group the combinations into sorted rows per ID prefix."""
    shards: dict[str, list[list[str]]] = defaultdict(list)
    for facility in sorted(found):
        for combination in sorted(found[facility], key=lambda c: tuple(float(v) for v in c)):
            shards[facility[:prefix_digits]].append([facility, *combination])
    return dict(shards)


def write_shards(shards: dict[str, list[list[str]]], nei: NeiSettings, target: Path) -> list[Path]:
    """Replace the shard files in ``target`` with ``shards``; return the files written."""
    pattern = nei.file_template.format(prefix="*")
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob(pattern):
        stale.unlink()
    names = [nei.id_column, *(nei.columns[q] for q in STACK_QUANTITIES)]
    written: list[Path] = []
    for prefix, rows in sorted(shards.items()):
        path = target / nei.file_template.format(prefix=prefix)
        path.write_bytes(to_gzip(names, rows))
        written.append(path)
    return written


def main(argv: Sequence[str]) -> int:
    """Build the shards from ``argv[0]`` (default: the configured zip) into ``argv[1]``."""
    nei = get_stack_settings().nei
    raw = Path(argv[0]) if argv else nei.raw_path
    target = Path(argv[1]) if len(argv) > 1 else nei.directory
    try:
        shards = shard_rows(read_combinations(raw, nei), nei.prefix_digits)
    except (OSError, ValueError, csv.Error, zipfile.BadZipFile) as exc:
        print(f"cannot compact the NEI stacks: {exc}", file=sys.stderr)
        return 1
    if not shards:
        print("no usable stack rows found; nothing written", file=sys.stderr)
        return 1
    files = write_shards(shards, nei, target)
    rows = sum(len(r) for r in shards.values())
    print(f"wrote {rows} rows to {len(files)} shards in {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
