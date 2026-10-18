"""Emissions inventory query tool."""

from __future__ import annotations

import logging

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from config.loader import get_emissions_settings, get_tri_settings, get_unit_settings
from tools.emissions.helpers.lookup import lookup_emissions
from tools.emissions.helpers.tri import TriFetcher
from tools.schemas import EmissionRecord

logger = logging.getLogger(__name__)


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


@tool
def query_emissions_inventory(cas_number: str) -> list[EmissionRecord]:
    """List facilities that reported emitting a chemical, with their latest reported release.

    Purpose:
        Use this to discover emission sources of a chemical from the EPA Toxics Release
        Inventory (TRI). For each facility it uses the most recent year the facility
        reported, so different facilities may be reported for different years. Only
        stack (point-source) air releases are returned; fugitive air, water and land
        releases are not. Each result's `frs_id` identifies the facility for
        `get_facility_metadata` and `fetch_stack_parameters_from_nei`, and `emission_rate` feeds
        `calculate_exposure_metrics`. A widely reported chemical can take several minutes
        because TRI is read in many pages.

    Args:
        cas_number: CAS registry number, e.g. "50-00-0" (hyphens optional).

    Returns:
        A list of dicts, one per facility (empty if none, if the CAS number is invalid, or
        if TRI could not be read), each with:
        - frs_id: EPA Facility Registry Service identifier
        - facility_name: facility display name (may be null)
        - environmental_medium: TRI release medium, e.g. "AIR STACK"
        - reporting_year: latest year the facility reported for that medium
        - total_release: quantity released in that year, in `unit` per year, as reported
        - unit: unit of `total_release` as reported by TRI, e.g. "Pounds"
        - emission_rate: average emission rate, g/s, assuming the facility operates
          `operating_hours_per_year`
        - operating_hours_per_year: hours per year assumed for `emission_rate` (8760 =
          continuous operation, a conservative screening assumption)
        - latitude, longitude: decimal degrees (negative longitude is west)
        - address, city, county, state, zip_code: facility location (each may be null)
    """
    cas = format_cas(cas_number)
    if cas is None:
        logger.warning("query_emissions_inventory: %r is not a valid CAS number", cas_number)
        return []
    tri = get_tri_settings()
    with _open_client() as client:
        fetcher = TriFetcher(tri, client)
        return lookup_emissions(
            cas, tri, get_emissions_settings(), get_unit_settings().aliases, fetcher
        )
