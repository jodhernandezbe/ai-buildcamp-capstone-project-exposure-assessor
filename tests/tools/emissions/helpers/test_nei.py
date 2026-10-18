"""Tests for tools.emissions.helpers.nei (synthetic shards: fake IDs, round numbers)."""

from __future__ import annotations

import gzip
import os
from dataclasses import replace
from pathlib import Path

import pytest

from config.stack import StackSettings, load_stack_settings
from tools.emissions.helpers.nei import build_candidates

HEADER = "eis_id,stkhgt,stkdiam,stkvel,stktemp\n"
FEET = 0.3048


def _settings(tmp_path: Path, **nei: int) -> StackSettings:
    base = load_stack_settings()
    changes = {"prefix_digits": 1, "max_candidates": 3, "merge_significant_digits": 2, **nei}
    return replace(base, nei=replace(base.nei, directory=tmp_path, **changes))


def _shard(tmp_path: Path, prefix: str, rows: str, header: str = HEADER) -> Path:
    path = tmp_path / f"nei_stacks_{prefix}.csv.gz"
    path.write_bytes(gzip.compress((header + rows).encode()))
    return path


def _heights(tmp_path: Path, ids: list[str], **nei: int) -> list[float]:
    found = build_candidates(ids, _settings(tmp_path, **nei), None)
    return [round(s["stack_height"] / FEET) for s in found.stacks]


def test_one_stack_is_converted_to_si(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n")
    found = build_candidates(["1000001"], _settings(tmp_path), None)
    assert found.warnings == ()
    assert found.total == 1
    (stack,) = found.stacks
    assert stack["stack_height"] == pytest.approx(3.048)
    assert stack["stack_diameter"] == pytest.approx(0.9144)
    assert stack["exit_velocity"] == pytest.approx(3.048)
    assert stack["exit_temperature"] == pytest.approx(366.4833, abs=1e-3)


def test_identical_rows_of_two_ids_collapse(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n1000002,10,3,10,200\n")
    found = build_candidates(["1000001", "1000002"], _settings(tmp_path), None)
    assert (len(found.stacks), found.total) == (1, 1)
    assert "1 near-identical merged" in found.warnings[0]


def test_near_identical_stacks_merge_but_keep_real_values(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,99,3,10,200\n1000001,99.5,3,10,200\n1000001,120,3,10,200\n")
    found = build_candidates(["1000001"], _settings(tmp_path), None)
    assert found.total == 2
    assert found.stacks[0]["stack_height"] == pytest.approx(99 * FEET)  # the first row's value
    assert "1 near-identical merged" in found.warnings[0]


def test_ordered_lowest_stack_first_then_velocity_temperature_diameter(tmp_path: Path) -> None:
    _shard(
        tmp_path,
        "1",
        "1000001,30,3,10,200\n"
        "1000001,10,3,50,200\n"
        "1000001,10,3,20,300\n"
        "1000001,10,3,20,200\n"
        "1000001,10,5,20,200\n",
    )
    found = build_candidates(["1000001"], _settings(tmp_path, max_candidates=10), None)
    order = [
        (
            round(s["stack_height"] / FEET),
            round(s["exit_velocity"] / FEET),
            round((s["exit_temperature"] - 273.15) * 9 / 5 + 32),
            round(s["stack_diameter"] / FEET),
        )
        for s in found.stacks
    ]
    assert order == [
        (10, 20, 200, 3),
        (10, 20, 200, 5),
        (10, 20, 300, 3),
        (10, 50, 200, 3),
        (30, 10, 200, 3),
    ]


def test_cap_keeps_the_lowest_and_reports_the_rest(tmp_path: Path) -> None:
    rows = "".join(f"1000001,{h},3,10,200\n" for h in (50, 20, 40, 10, 30))
    _shard(tmp_path, "1", rows)
    found = build_candidates(["1000001"], _settings(tmp_path), None)
    assert [round(s["stack_height"] / FEET) for s in found.stacks] == [10, 20, 30]
    assert found.total == 5
    assert "5 distinct" in found.warnings[0]
    assert "2 taller omitted" in found.warnings[0]


def test_no_summary_when_nothing_merged_or_omitted(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n1000001,20,3,10,200\n")
    assert build_candidates(["1000001"], _settings(tmp_path), None).warnings == ()


@pytest.mark.parametrize(
    "bad",
    [
        "1000001,,3,10,200",  # blank height
        "1000001,abc,3,10,200",  # not a number
        "1000001,10,3,10,",  # blank temperature
        "1000001,0,3,10,200",  # zero height
        "1000001,-10,3,10,200",  # negative
        "1000001,10,3,10,nan",  # not finite
        "1000001,10,3,10,5000",  # temperature above the plausible range
        "1000001,10000,3,10,200",  # height above the plausible range
        "1000001,10,3,0,200",  # zero velocity
    ],
)
def test_invalid_rows_are_dropped_and_counted(tmp_path: Path, bad: str) -> None:
    _shard(tmp_path, "1", bad + "\n1000001,20,3,10,200\n")
    found = build_candidates(["1000001"], _settings(tmp_path), None)
    assert [round(s["stack_height"] / FEET) for s in found.stacks] == [20]
    assert found.warnings == (
        "1 NEI stack row(s) were ignored: a value was missing or implausible",
    )


def test_a_row_is_never_repaired_from_another(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,,200\n1000001,,3,10,200\n")
    found = build_candidates(["1000001"], _settings(tmp_path), None)
    assert found.stacks == ()
    assert "2 NEI stack row(s) were ignored" in found.warnings[0]


def test_id_absent_from_the_table(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n")
    found = build_candidates(["1999999"], _settings(tmp_path), None)
    assert found.stacks == ()
    assert found.warnings == ("the NEI table has no stack data for EIS ID 1999999",)


def test_ids_of_different_shards_are_combined(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n")
    _shard(tmp_path, "2", "2000002,20,3,10,200\n")
    assert _heights(tmp_path, ["1000001", "2000002"]) == [10, 20]


def test_only_the_shard_of_the_prefix_is_read(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n")
    (tmp_path / "nei_stacks_2.csv.gz").write_bytes(b"not gzip")  # never opened
    assert _heights(tmp_path, ["1000001"]) == [10]


def test_prefix_digits_choose_the_shard(tmp_path: Path) -> None:
    _shard(tmp_path, "10", "1000001,10,3,10,200\n")
    assert _heights(tmp_path, ["1000001"], prefix_digits=2) == [10]


@pytest.mark.parametrize("content", [None, b"not gzip", gzip.compress(b"x" * 1000)[:20]])
def test_unreadable_shard_is_a_warning(tmp_path: Path, content: bytes | None) -> None:
    if content is not None:
        (tmp_path / "nei_stacks_1.csv.gz").write_bytes(content)
    found = build_candidates(["1000001", "2000002"], _settings(tmp_path), None)
    assert found.stacks == ()
    assert "nei_stacks_1.csv.gz could not be read" in found.warnings[0]


def test_one_bad_shard_does_not_hide_a_good_one(tmp_path: Path) -> None:
    _shard(tmp_path, "2", "2000002,20,3,10,200\n")
    found = build_candidates(["1000001", "2000002"], _settings(tmp_path), None)
    assert [round(s["stack_height"] / FEET) for s in found.stacks] == [20]
    assert "could not be read" in found.warnings[0]


def test_missing_configured_column_raises(tmp_path: Path) -> None:
    _shard(tmp_path, "1", "1000001,10,3,10,200\n", HEADER.replace("stkvel", "vel"))
    with pytest.raises(ValueError, match="stkvel"):
        build_candidates(["1000001"], _settings(tmp_path), None)


def test_unconvertible_unit_raises(tmp_path: Path) -> None:
    base = _settings(tmp_path)
    units = {**base.nei.units, "stack_height": "kg"}
    settings = replace(base, nei=replace(base.nei, units=units))
    with pytest.raises(ValueError, match="stack_height"):
        build_candidates(["1000001"], settings, None)


def test_changed_file_is_read_again(tmp_path: Path) -> None:
    path = _shard(tmp_path, "1", "1000001,10,3,10,200\n")
    assert _heights(tmp_path, ["1000001"]) == [10]
    _shard(tmp_path, "1", "1000001,50,3,10,200\n")
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert _heights(tmp_path, ["1000001"]) == [50]


def test_unit_conversion_follows_the_configured_units(tmp_path: Path) -> None:
    base = _settings(tmp_path)
    units = {q: u for q, u in zip(base.nei.units, ("m", "m", "m/s", "K"), strict=True)}
    settings = replace(base, nei=replace(base.nei, units=units))
    _shard(tmp_path, "1", "1000001,10,3,10,300\n")
    (stack,) = build_candidates(["1000001"], settings, None).stacks
    assert (stack["stack_height"], stack["exit_temperature"]) == (10.0, 300.0)
