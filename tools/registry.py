"""Central tool registry: every tool the agent can bind, exported as one list."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from tools.emissions import TOOLS as EMISSIONS_TOOLS
from tools.exposure import TOOLS as EXPOSURE_TOOLS
from tools.geospatial import TOOLS as GEOSPATIAL_TOOLS
from tools.informatics import TOOLS as INFORMATICS_TOOLS


class ToolRegistry:
    """Ordered collection of tools, keyed by tool name."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, *tools: BaseTool) -> None:
        """Add tools; raises ``ValueError`` on duplicate names."""
        for t in tools:
            if t.name in self._tools:
                raise ValueError(f"Tool already registered: {t.name}")
            self._tools[t.name] = t

    def get(self, name: str) -> BaseTool:
        """Return the tool called ``name``; raises ``KeyError`` if unknown."""
        return self._tools[name]

    def all(self) -> list[BaseTool]:
        """Return all registered tools in registration order."""
        return list(self._tools.values())


def _build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        *INFORMATICS_TOOLS,
        *EMISSIONS_TOOLS,
        *GEOSPATIAL_TOOLS,
        *EXPOSURE_TOOLS,
    )
    return registry


registry: ToolRegistry = _build_default_registry()

ALL_TOOLS: list[BaseTool] = registry.all()


def get_all_tools() -> list[BaseTool]:
    """Return every registered tool, ready to pass to ``model.bind_tools``."""
    return registry.all()
