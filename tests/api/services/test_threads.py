"""Tests for the in-memory thread store."""

from __future__ import annotations

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
