"""Geospatial tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.geospatial.metadata import get_facility_metadata

TOOLS: list[BaseTool] = [get_facility_metadata]

__all__ = ["TOOLS", "get_facility_metadata"]
