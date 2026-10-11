"""Chemical informatics tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.informatics.properties import fetch_chemical_properties

TOOLS: list[BaseTool] = [fetch_chemical_properties]

__all__ = ["TOOLS", "fetch_chemical_properties"]
