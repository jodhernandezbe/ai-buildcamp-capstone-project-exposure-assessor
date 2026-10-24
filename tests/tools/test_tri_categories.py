"""Tests for the TRI category member index."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.tri_categories import TriCategoriesSettings
from tools.tri_categories import CategoryIndex, load_index

HEADER = "CAS NUMBER,CATEGORY CODE,CATEGORY NAME,CHEMICAL NAME,CHEMICAL TYPE,SOURCE"


def _settings(path: Path) -> TriCategoriesSettings:
    return TriCategoriesSettings(
        path, "CAS NUMBER", "CATEGORY CODE", "CATEGORY NAME", "CHEMICAL NAME", "CHEMICAL TYPE",
        "Organic",
    )  # fmt: skip


def _index(tmp_path: Path, *rows: str) -> CategoryIndex:
    path = tmp_path / "cats.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return load_index(_settings(path))


def test_single_category(tmp_path: Path) -> None:
    index = _index(tmp_path, "95-57-8,N084,CHLOROPHENOLS,2-chlorophenol,Organic,x")
    (category,) = index.lookup("95-57-8").categories
    assert (category.code, category.name) == ("N084", "CHLOROPHENOLS")


def test_group_code_is_kept_and_digit_code_is_hyphenated(tmp_path: Path) -> None:
    index = _index(
        tmp_path,
        "7439-92-1,N420,LEAD COMPOUNDS,lead,Inorganic,x",
        "1336-36-3,1336363,Polychlorinated biphenyls,PCB,Organic,x",
    )
    assert index.codes == {"N420", "1336-36-3"}


def test_several_categories_are_all_returned_in_file_order(tmp_path: Path) -> None:
    index = _index(
        tmp_path,
        "544-92-3,N100,COPPER COMPOUNDS,copper cyanide,Inorganic,x",
        "544-92-3,N106,CYANIDE COMPOUNDS,copper cyanide,Inorganic,x",
        "544-92-3,N100,COPPER COMPOUNDS,copper cyanide,Inorganic,x",
    )
    assert [c.code for c in index.lookup("544-92-3").categories] == ["N100", "N106"]


def test_not_a_member_returns_nothing(tmp_path: Path) -> None:
    index = _index(tmp_path, "95-57-8,N084,CHLOROPHENOLS,2-chlorophenol,Organic,x")
    lookup = index.lookup("110-54-3")
    assert lookup.categories == () and lookup.warnings == ()


def test_invalid_cas_in_query_warns(tmp_path: Path) -> None:
    index = _index(tmp_path, "95-57-8,N084,CHLOROPHENOLS,2-chlorophenol,Organic,x")
    lookup = index.lookup("110-54-4")
    assert lookup.categories == () and "not valid" in lookup.warnings[0]


def test_row_with_bad_check_digit_is_dropped_and_counted(tmp_path: Path) -> None:
    index = _index(
        tmp_path,
        "95-57-9,N084,CHLOROPHENOLS,2-chlorophenol,Organic,x",
        "0592-01-08,N106,CYANIDE COMPOUNDS,Calcium cyanide,Inorganic,x",
    )
    assert index.members == {} and index.dropped == {"invalid CAS number": 2}


def test_row_with_empty_or_invalid_code_is_dropped(tmp_path: Path) -> None:
    index = _index(
        tmp_path,
        "95-57-8,,CHLOROPHENOLS,2-chlorophenol,Organic,x",
        "108-43-0,1234567,X,3-chlorophenol,Organic,x",
    )
    assert index.members == {} and sum(index.dropped.values()) == 2


def test_organic_is_true_if_any_row_is_organic(tmp_path: Path) -> None:
    index = _index(
        tmp_path,
        "95-57-8,N084,A,x,Inorganic,x",
        "95-57-8,N085,B,x,Organic,x",
    )
    assert index.members["95-57-8"].organic


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_index(_settings(tmp_path / "nope.csv"))


def test_missing_column_raises(tmp_path: Path) -> None:
    path = tmp_path / "cats.csv"
    path.write_text("CAS NUMBER\n95-57-8\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CATEGORY CODE"):
        load_index(_settings(path))


def test_members_cannot_be_changed(tmp_path: Path) -> None:
    index = _index(tmp_path, "95-57-8,N084,A,x,Organic,x")
    with pytest.raises(TypeError):
        index.members["1-1-1"] = index.members["95-57-8"]  # type: ignore[index]
