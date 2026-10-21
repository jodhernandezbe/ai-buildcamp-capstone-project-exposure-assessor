"""Emissions inventory query tool."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from config.efservice import get_efservice_settings
from config.frs_point import get_frs_point_settings
from config.loader import get_emissions_settings, get_tri_settings, get_unit_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.frs_point import FrsLocator
from tools.emissions.helpers.inventory.listing import rank_and_cap
from tools.emissions.helpers.inventory.lookup import lookup_emissions
from tools.emissions.helpers.inventory.tri import TriFetcher
from tools.schemas import EmissionRecord, InventoryResult

logger = logging.getLogger(__name__)


def _current_year() -> int:
    """Return the current calendar year (the edge where the clock is read)."""
    return date.today().year


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


def _frs_locator(client: httpx.Client) -> FrsLocator:
    """The bulk coordinates lookup: the shared request policy on the FRS service's own URL."""
    frs = get_frs_point_settings()
    service = replace(get_efservice_settings(), base_url=frs.base_url)
    return FrsLocator(EfserviceClient(service, client), frs)


@tool(response_format="content_and_artifact")
def query_emissions_inventory(
    cas_number: str, state: str | None = None, city: str | None = None
) -> tuple[InventoryResult, list[EmissionRecord]]:
    """List facilities that reported emitting a chemical, with their latest reported release.

    Purpose:
        Use this to discover emission sources of a chemical from the EPA Toxics Release
        Inventory (TRI). For each facility it uses the most recent year the facility
        reported, so different facilities may be reported for different years. Only
        stack (point-source) air releases are returned; fugitive air, water and land
        releases are not. Each result carries the facility's location (latitude, longitude,
        address), its `frs_id` identifies the facility for `fetch_stack_parameters_from_nei`,
        and `emission_rate` feeds `calculate_exposure_metrics`. A widely reported chemical
        can take a while because TRI is read in many pages (facilities without TRI coordinates
        are then located in FRS, many per request) and may have over a thousand facilities.
        Only the largest are listed to you, highest `emission_rate` first, so the first
        facilities listed are the largest sources; `total_found`, `matching` and `note` say how
        many more there are. Never present a list as complete when `note` says it is partial.
        To look at a place, call again with `state` and/or `city`: the largest facilities there
        are listed. Decide which facilities to assess rather than assessing all. TRI gives
        only each facility's primary NAICS code, nothing about its process;
        `fetch_facility_industry` gives that industry in words for a facility you choose, and
        the process is only a candidate derived from it.
        Zero facilities means no stack air release was found for this CAS number (and place) in
        TRI, which is not evidence that nobody emits it: TRI covers only facilities above its
        reporting thresholds.

    Args:
        cas_number: CAS registry number as the user gave it, e.g. "50-00-0" (hyphens
            optional). Never a number recalled from a chemical's name: if the user gave only a
            name, ask for the CAS number instead of calling this tool.
        state: Optional. Keep only facilities in this state, as its two-letter postal
            abbreviation, e.g. "TX".
        city: Optional. Keep only facilities in this city, by its exact name, e.g. "Houston"
            (a metropolitan area spans several city names; use `state` for a wider look).

    Returns:
        A dict with:
        - total_found: facilities found for this chemical, before `state` and `city`
        - matching: facilities that match `state` and `city` (all of them when none is given)
        - shown: facilities listed in `facilities`
        - note: says that the list is partial and how to see others; null when it is complete
        - facilities: the largest matching facilities, highest `emission_rate` first (empty if
          none, if the CAS number is invalid, or if TRI could not be read), each with:
          - frs_id: EPA Facility Registry Service identifier
          - facility_name: facility display name (may be null)
          - environmental_medium: TRI release medium, e.g. "AIR STACK"
          - reporting_year: latest year the facility reported for that medium (only the last 2
            reporting years are searched, so a facility that stopped reporting earlier is
            absent)
          - doc_ctrl_num: TRI control number of that year's submission; pass it to
            `fetch_facility_industry` to learn the facility's industry (null if TRI gave none)
          - naics_code: primary NAICS code of that submission, digits only (null if TRI gave
            none); `fetch_facility_industry` gives its title in words, which the SCC process
            search needs, and whether the facility reported it or EPA assigned it
          - total_release: quantity released in that year, in `unit` per year, as reported
          - unit: unit of `total_release` as reported by TRI, e.g. "Pounds"
          - emission_rate: average emission rate, g/s, assuming the facility operates
            `operating_hours_per_year`
          - operating_hours_per_year: hours per year assumed for `emission_rate` (8760 =
            continuous operation, a conservative screening assumption)
          - latitude, longitude: decimal degrees (negative longitude is west); from TRI, or
            from the facility's FRS record when TRI has none
          - address, city, county, state, zip_code: facility location (each may be null)
    """
    cas = format_cas(cas_number)
    if cas is None:
        logger.warning("query_emissions_inventory: %r is not a valid CAS number", cas_number)
        return rank_and_cap([], get_tri_settings().max_listed, state, city)
    tri = get_tri_settings()
    year = _current_year()
    with _open_client() as client:
        ef = EfserviceClient(get_efservice_settings(), client)
        records = lookup_emissions(
            cas,
            tri,
            get_emissions_settings(),
            get_unit_settings().aliases,
            TriFetcher(tri, ef, year),
            year,
            _frs_locator(client),
        )
    return rank_and_cap(records, tri.max_listed, state, city)
