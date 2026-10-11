"""Tests for query_emissions_inventory."""

from __future__ import annotations

import pytest

from tools.emissions.inventory import query_emissions_inventory


def test_schema() -> None:
    assert query_emissions_inventory.name == "query_emissions_inventory"
    assert set(query_emissions_inventory.args) == {"cas_number", "reporting_year"}
    assert query_emissions_inventory.description


def test_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        query_emissions_inventory.invoke({"cas_number": "71-43-2", "reporting_year": 2022})
