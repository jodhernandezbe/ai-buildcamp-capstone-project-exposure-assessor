"""Tests for scripts.compact_scc_table."""

from __future__ import annotations

import csv
import gzip
from dataclasses import replace
from pathlib import Path

import pytest

from config.retrieval import load_scc_index_settings
from scripts.compact_scc_table import compact_rows, main, to_gzip

RAW_HEADER = (
    "SCC,extra one,data category,status,scc level one,scc level two,scc level three,"
    "scc level four,sector,extra two\n"
)
RAW_ROWS = (
    "99900001,a,Point,Active,L1,L2,L3,L4a,Sector A,x\n"
    '99900002,b,Nonpoint,Active,L1,L2,L3,"L4, with comma",Sector B,y\n'
    "99900003,c,Point,Retired,L1,L2,L3,L4c,Sector C,z\n"
    "99900004,d,Onroad,Active,L1,L2,L3,L4d,Sector D,w\n"
)
COLUMNS = [
    "SCC",
    "data category",
    "status",
    "scc level one",
    "scc level two",
    "scc level three",
    "scc level four",
    "sector",
]


def _raw(tmp_path: Path, text: str = RAW_HEADER + RAW_ROWS) -> Path:
    path = tmp_path / "raw.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_keeps_only_configured_columns_and_categories(tmp_path: Path) -> None:
    names, rows = compact_rows(_raw(tmp_path), load_scc_index_settings())
    assert names == COLUMNS
    assert [row[0] for row in rows] == ["99900001", "99900003"]  # Point only; statuses kept
    assert rows[0] == ["99900001", "Point", "Active", "L1", "L2", "L3", "L4a", "Sector A"]


def test_categories_come_from_settings(tmp_path: Path) -> None:
    settings = replace(load_scc_index_settings(), categories=("Point", "Onroad"))
    _, rows = compact_rows(_raw(tmp_path), settings)
    assert [row[0] for row in rows] == ["99900001", "99900003", "99900004"]


def test_missing_column_raises(tmp_path: Path) -> None:
    text = RAW_HEADER.replace("sector,", "sectr,") + RAW_ROWS
    with pytest.raises(ValueError, match="lacks configured columns: sector"):
        compact_rows(_raw(tmp_path, text), load_scc_index_settings())


def test_blank_cells_stay_blank(tmp_path: Path) -> None:
    text = RAW_HEADER + "99900005,a,Point,Active,L1,,,L4,,x\n"
    _, rows = compact_rows(_raw(tmp_path, text), load_scc_index_settings())
    assert rows[0][4:] == ["", "", "L4", ""]


def test_gzip_is_deterministic_and_round_trips() -> None:
    rows = [["1", "Point", "Active", "a, b", "c", "d", "e", "é"]]
    first, second = to_gzip(COLUMNS, rows), to_gzip(COLUMNS, rows)
    assert first == second
    text = gzip.decompress(first).decode("utf-8")
    assert list(csv.reader(text.splitlines())) == [COLUMNS, *rows]
    assert "\r" not in text


def test_main_writes_the_table(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "out" / "scc.csv.gz"
    assert main([str(_raw(tmp_path)), str(target)]) == 0
    text = gzip.decompress(target.read_bytes()).decode("utf-8")
    assert text.splitlines()[0] == ",".join(COLUMNS)
    assert len(text.splitlines()) == 3
    assert "wrote 2 rows x 8 columns" in capsys.readouterr().out


def test_main_fails_without_writing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "scc.csv.gz"
    assert main([str(tmp_path / "absent.csv"), str(target)]) == 1
    assert main([str(_raw(tmp_path, RAW_HEADER)), str(target)]) == 1  # no rows
    bad = _raw(tmp_path, RAW_HEADER.replace("sector,", "sectr,") + RAW_ROWS)
    assert main([str(bad), str(target)]) == 1
    assert not target.exists()
    assert capsys.readouterr().err.count("cannot compact") + 1 >= 2
