"""Industrial emissions tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.emissions.inventory import query_emissions_inventory
from tools.emissions.stack import fetch_stack_parameters

TOOLS: list[BaseTool] = [query_emissions_inventory, fetch_stack_parameters]

__all__ = ["TOOLS", "fetch_stack_parameters", "query_emissions_inventory"]
