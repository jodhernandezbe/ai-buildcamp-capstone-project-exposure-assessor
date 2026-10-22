"""Fixtures shared by the whole suite."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from tools.emissions.inventory import clear_inventory_cache


@pytest.fixture(autouse=True)
def fresh_inventory_cache() -> Iterator[None]:
    """Each test reads its own (mocked) TRI: no inventory is reused from another test."""
    clear_inventory_cache()
    yield
    clear_inventory_cache()
