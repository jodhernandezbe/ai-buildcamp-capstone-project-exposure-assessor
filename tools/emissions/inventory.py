"""Emissions inventory query tool."""

from __future__ import annotations

import logging

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from config.efservice import get_efservice_settings
from config.loader import get_emissions_settings, get_tri_settings, get_unit_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.lookup import lookup_emissions
from tools.emissions.helpers.inventory.tri import TriFetcher
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
        releases are not. Each result carries the facility's location (latitude, longitude,
        address), its `frs_id` identifies the facility for `fetch_stack_parameters_from_nei`,
        and `emission_rate` feeds `calculate_exposure_metrics`. A widely reported chemical
        can take several minutes because TRI is read in many pages and may return hundreds
        of facilities, so decide which to assess rather than assessing all. TRI says nothing
        about a facility's industry or process (those are needed only for generic stack
        defaults and must come from the user or be left unknown). An empty list means no
        stack air release was found for this CAS number in TRI, which is not evidence that
        nobody emits it: TRI covers only facilities above its reporting thresholds.

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
        fetcher = TriFetcher(tri, EfserviceClient(get_efservice_settings(), client))
        return lookup_emissions(
            cas, tri, get_emissions_settings(), get_unit_settings().aliases, fetcher
        )
