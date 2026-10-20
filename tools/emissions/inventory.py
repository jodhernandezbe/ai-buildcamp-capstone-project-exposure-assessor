"""Emissions inventory query tool."""

from __future__ import annotations

import logging
from datetime import date

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from config.efservice import get_efservice_settings
from config.frs_point import get_frs_point_settings
from config.loader import get_emissions_settings, get_tri_settings, get_unit_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.frs_point import FrsLocator
from tools.emissions.helpers.inventory.lookup import lookup_emissions
from tools.emissions.helpers.inventory.tri import TriFetcher
from tools.schemas import EmissionRecord

logger = logging.getLogger(__name__)


def _current_year() -> int:
    """Return the current calendar year (the edge where the clock is read)."""
    return date.today().year


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
        can take several minutes because TRI is read in many pages (and a facility without TRI
        coordinates costs one more request to find them in FRS) and may return hundreds
        of facilities, so decide which to assess rather than assessing all. TRI says nothing
        about a facility's industry or process; `fetch_facility_industry` gives the industry
        of a facility you choose, and the process is only a candidate derived from it. An
        empty list means no stack air release was found for this CAS number in TRI, which is
        not evidence that nobody emits it: TRI covers only facilities above its reporting
        thresholds.

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "50-00-0" (hyphens
            optional). Never a number recalled from a chemical's name: if the user gave only a
            name, ask for the CAS number instead of calling this tool.

    Returns:
        A list of dicts, one per facility (empty if none, if the CAS number is invalid, or
        if TRI could not be read), each with:
        - frs_id: EPA Facility Registry Service identifier
        - facility_name: facility display name (may be null)
        - environmental_medium: TRI release medium, e.g. "AIR STACK"
        - reporting_year: latest year the facility reported for that medium (only the last 10
          reporting years are searched, so a facility that stopped reporting earlier is absent)
        - doc_ctrl_num: TRI control number of that year's submission; pass it to
          `fetch_facility_industry` to learn the facility's industry (null if TRI gave none)
        - total_release: quantity released in that year, in `unit` per year, as reported
        - unit: unit of `total_release` as reported by TRI, e.g. "Pounds"
        - emission_rate: average emission rate, g/s, assuming the facility operates
          `operating_hours_per_year`
        - operating_hours_per_year: hours per year assumed for `emission_rate` (8760 =
          continuous operation, a conservative screening assumption)
        - latitude, longitude: decimal degrees (negative longitude is west); from TRI, or from the
          facility's FRS record when TRI has none
        - address, city, county, state, zip_code: facility location (each may be null)
    """
    cas = format_cas(cas_number)
    if cas is None:
        logger.warning("query_emissions_inventory: %r is not a valid CAS number", cas_number)
        return []
    tri = get_tri_settings()
    year = _current_year()
    with _open_client() as client:
        ef = EfserviceClient(get_efservice_settings(), client)
        locate = FrsLocator(ef, get_frs_point_settings())
        return lookup_emissions(
            cas,
            tri,
            get_emissions_settings(),
            get_unit_settings().aliases,
            TriFetcher(tri, ef, year),
            year,
            locate,
        )
