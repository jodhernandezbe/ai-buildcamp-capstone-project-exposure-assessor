"""Tests for the tool and prompt registries."""

from __future__ import annotations

import pytest

from tools.registry import ToolRegistry, get_all_tools


def test_all_tools_registered_with_docstrings() -> None:
    tools = get_all_tools()
    assert {t.name for t in tools} == {
        "fetch_chemical_properties",
        "find_tri_read_across_surrogate",
        "query_emissions_inventory",
        "fetch_facility_industry",
        "lookup_scc_process_description",
        "fetch_stack_parameters_from_nei",
        "fetch_stack_parameters_from_scc",
        "get_meteorological_boundary",
        "get_population_receptors",
        "calculate_exposure_metrics",
        "assess_facilities",
    }
    assert all(t.description for t in tools)


def test_duplicate_registration_rejected() -> None:
    reg = ToolRegistry()
    tool = get_all_tools()[0]
    reg.register(tool)
    with pytest.raises(ValueError):
        reg.register(tool)
