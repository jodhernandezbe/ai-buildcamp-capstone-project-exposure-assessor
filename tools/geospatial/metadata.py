"""Facility metadata tool."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import FacilityMetadata


@tool
def get_facility_metadata(frs_id: str) -> FacilityMetadata:
    """Get the location and process classification of a facility.

    Purpose:
        Use this to turn a facility identifier into coordinates for the
        meteorology and population lookups, and into the SCC code needed by
        `fetch_stack_parameters`.

    Args:
        frs_id: EPA Facility Registry Service identifier.

    Returns:
        A dict with:
        - latitude: decimal degrees (WGS84)
        - longitude: decimal degrees (WGS84)
        - address: street address of the facility
        - scc_code: Source Classification Code of the primary emitting process
    """
    raise NotImplementedError
