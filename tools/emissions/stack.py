"""Stack parameter lookup tool."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import StackParameters


@tool
def fetch_stack_parameters(frs_id: str, scc_code: str) -> StackParameters:
    """Fetch release-point (stack) geometry and exit conditions for a facility.

    Purpose:
        Plume rise and dispersion depend on stack geometry. Use this after
        identifying a facility and its process classification.

    Args:
        frs_id: EPA Facility Registry Service identifier of the facility.
        scc_code: Source Classification Code of the emitting process, as returned
            by `get_facility_metadata`.

    Returns:
        A dict with:
        - stack_height: m above ground
        - stack_diameter: m
        - exit_velocity: m/s
        - exit_temperature: K
    """
    raise NotImplementedError
