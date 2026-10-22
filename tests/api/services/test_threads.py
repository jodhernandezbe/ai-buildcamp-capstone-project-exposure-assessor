"""Tests for the in-memory thread store."""

from __future__ import annotations

import pytest

from api.services.threads import ThreadStore


def test_one_turn_at_a_time_per_thread() -> None:
    threads = ThreadStore()
    assert threads.claim("a") is True
    assert threads.claim("a") is False
    assert threads.claim("b") is True
    threads.release("a")
    assert threads.claim("a") is True


def test_release_is_idempotent() -> None:
    threads = ThreadStore()
    threads.release("never-claimed")
    assert threads.claim("x") is True


def test_reset_is_refused_while_busy() -> None:
    threads = ThreadStore()
    threads.claim("a")
    assert threads.reset("a") is False
    threads.release("a")
    assert threads.reset("a") is True


def test_least_recently_used_idle_thread_is_forgotten_past_the_limit() -> None:
    threads = ThreadStore(max_threads=2)
    for name in ("a", "b"):
        threads.claim(name)
        threads.release(name)
    threads.touch("a")  # b is now the oldest
    threads.claim("c")
    assert (threads.holds("a"), threads.holds("b"), threads.holds("c")) == (True, False, True)


def test_a_running_thread_is_never_forgotten() -> None:
    threads = ThreadStore(max_threads=1)
    threads.claim("a")
    threads.claim("b")
    assert threads.holds("a") and threads.holds("b")
    threads.release("a")
    threads.claim("c")
    assert not threads.holds("a")


def test_no_limit_keeps_every_thread() -> None:
    threads = ThreadStore()
    for name in "abcdef":
        threads.claim(name)
        threads.release(name)
    assert all(threads.holds(name) for name in "abcdef")


def test_reset_forgets_the_thread() -> None:
    threads = ThreadStore()
    threads.claim("a")
    threads.release("a")
    assert threads.reset("a") is True
    assert threads.holds("a") is False


def test_the_limit_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_threads"):
        ThreadStore(max_threads=0)


def test_messages_of_an_unknown_thread_are_empty() -> None:
    assert ThreadStore().messages("nope") == []
