"""Tests for the context-scoped secret holder."""

from __future__ import annotations

import asyncio
import contextvars
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import SecretStr

from commons.scoped_secret import ScopedSecret

A = SecretStr("secret-a")
B = SecretStr("secret-b")


def test_empty_outside_a_block() -> None:
    assert ScopedSecret("t").get() is None


def test_visible_inside_and_cleared_after() -> None:
    holder = ScopedSecret("t")
    with holder.provide(A):
        assert holder.get() is A
    assert holder.get() is None


def test_cleared_even_when_the_block_raises() -> None:
    holder = ScopedSecret("t")
    with pytest.raises(RuntimeError), holder.provide(A):
        raise RuntimeError("boom")
    assert holder.get() is None


def test_follows_copied_context_into_threads() -> None:
    holder = ScopedSecret("t")
    with holder.provide(A), ThreadPoolExecutor(1) as pool:
        seen = pool.submit(contextvars.copy_context().run, holder.get).result()
    assert seen is A


async def test_concurrent_tasks_do_not_see_each_other() -> None:
    holder = ScopedSecret("t")

    async def worker(secret: SecretStr) -> SecretStr | None:
        with holder.provide(secret):
            await asyncio.sleep(0.01)
            return holder.get()

    results = await asyncio.gather(worker(A), worker(B))
    assert results == [A, B]
    assert holder.get() is None


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
