"""Emissions inventory query tool."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import EmissionRecord


@tool
def query_emissions_inventory(cas_number: str, reporting_year: int) -> list[EmissionRecord]:
    """List facilities that reported emitting a chemical in a given year.

    Purpose:
        Use this to discover emission sources of a chemical (e.g. from the EPA
        Toxics Release Inventory). Each result's `frs_id` identifies the facility
        for `get_facility_metadata` and `fetch_stack_parameters`.

    Args:
        cas_number: CAS registry number, e.g. "71-43-2".
        reporting_year: Four-digit reporting year, e.g. 2022.

    Returns:
        A list of dicts, one per facility, each with:
        - frs_id: EPA Facility Registry Service identifier
        - facility_name: facility display name
        - emission_rate: annual-average emission rate, g/s
    """
    raise NotImplementedError
