"""Chemical informatics tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.informatics.properties import fetch_chemical_properties
from tools.informatics.read_across import find_tri_read_across_surrogate

TOOLS: list[BaseTool] = [fetch_chemical_properties, find_tri_read_across_surrogate]

__all__ = ["TOOLS", "fetch_chemical_properties", "find_tri_read_across_surrogate"]
