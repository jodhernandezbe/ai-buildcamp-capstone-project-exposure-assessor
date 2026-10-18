"""Industrial emissions tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.emissions.industry import fetch_facility_industry
from tools.emissions.inventory import query_emissions_inventory
from tools.emissions.process import lookup_scc_process_description
from tools.emissions.stack import fetch_stack_parameters_from_nei, fetch_stack_parameters_from_scc

TOOLS: list[BaseTool] = [
    query_emissions_inventory,
    fetch_facility_industry,
    lookup_scc_process_description,
    fetch_stack_parameters_from_nei,
    fetch_stack_parameters_from_scc,
]

__all__ = [
    "TOOLS",
    "fetch_facility_industry",
    "fetch_stack_parameters_from_nei",
    "fetch_stack_parameters_from_scc",
    "lookup_scc_process_description",
    "query_emissions_inventory",
]
