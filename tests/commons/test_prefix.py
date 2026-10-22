"""Tests for commons.prefix."""

from __future__ import annotations

from collections.abc import Iterator, Mapping

import pytest

from commons.prefix import longest_prefix

TABLE = {"325": 1, "3252": 2, "32521": 3, "3241": 4}


def test_exact_match() -> None:
    assert longest_prefix({"325211": 9, "3252": 2}, "325211", min_length=3) == ("325211", 9)


def test_falls_back_to_a_shorter_prefix() -> None:
    assert longest_prefix({"3252": 2, "325": 1}, "325211", min_length=3) == ("3252", 2)


def test_specific_beats_general() -> None:
    assert longest_prefix(TABLE, "325211", min_length=3) == ("32521", 3)


def test_never_matches_a_longer_table_key() -> None:
    assert longest_prefix({"325211": 9}, "3252", min_length=3) is None


def test_prefixes_below_the_minimum_are_ignored() -> None:
    assert longest_prefix({"32": 1}, "325211", min_length=3) is None
    assert longest_prefix({"32": 1}, "325211", min_length=2) == ("32", 1)


def test_no_match() -> None:
    assert longest_prefix(TABLE, "999999", min_length=3) is None


@pytest.mark.parametrize("key", ["", "3", "32"])
def test_key_shorter_than_the_minimum(key: str) -> None:
    assert longest_prefix(TABLE, key, min_length=3) is None


def test_invalid_minimum() -> None:
    with pytest.raises(ValueError, match="min_length"):
        longest_prefix(TABLE, "3252", min_length=0)


class _Counting(Mapping[str, int]):
    def __init__(self) -> None:
        self.probes: list[str] = []

    def __getitem__(self, key: str) -> int:
        raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        self.probes.append(str(key))
        return False

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("the table must not be scanned")

    def __len__(self) -> int:
        raise AssertionError("the table must not be scanned")


def test_probes_are_bounded_and_longest_first() -> None:
    table = _Counting()
    assert longest_prefix(table, "325211", min_length=3) is None
    assert table.probes == ["325211", "32521", "3252", "325"]
