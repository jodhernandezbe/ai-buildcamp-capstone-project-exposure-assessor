"""Tests for commons.ttl_cache."""

from __future__ import annotations

import pytest

from commons.ttl_cache import TtlCache


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_a_value_is_kept_for_its_time_and_then_forgotten() -> None:
    clock = Clock()
    cache: TtlCache[str, int] = TtlCache(10, clock=clock)
    cache.put("a", 1)
    clock.now = 9.9
    assert cache.get("a") == 1
    clock.now = 10.0
    assert cache.get("a") is None


def test_values_are_copies_both_ways() -> None:
    cache: TtlCache[str, list[int]] = TtlCache(10)
    stored = [1]
    cache.put("a", stored)
    stored.append(2)
    got = cache.get("a")
    assert got == [1]
    assert got is not None
    got.append(3)
    assert cache.get("a") == [1]


def test_the_oldest_entry_goes_when_full_and_a_read_keeps_one_fresh() -> None:
    cache: TtlCache[str, int] = TtlCache(10, max_entries=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert (cache.get("a"), cache.get("b"), cache.get("c")) == (1, None, 3)


def test_zero_seconds_keeps_nothing_and_clear_forgets() -> None:
    off: TtlCache[str, int] = TtlCache(0)
    off.put("a", 1)
    assert off.get("a") is None
    on: TtlCache[str, int] = TtlCache(10)
    on.put("a", 1)
    on.clear()
    assert on.get("a") is None


@pytest.mark.parametrize(("ttl", "size"), [(-1, 2), (1, 0)])
def test_bad_limits_are_refused(ttl: float, size: int) -> None:
    with pytest.raises(ValueError):
        TtlCache(ttl, max_entries=size)
