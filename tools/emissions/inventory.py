"""Emissions inventory query tool."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from functools import partial

import httpx
from langchain_core.tools import tool

from commons.cas import format_cas
from commons.ttl_cache import TtlCache
from config.assessment import get_assessment_settings
from config.efservice import get_efservice_settings
from config.frs_eis import get_frs_eis_settings
from config.frs_point import get_frs_point_settings
from config.industry import get_industry_settings
from config.loader import get_emissions_settings, get_tri_settings, get_unit_settings
from config.plant_hours import get_plant_hours_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.inventory.eis import UNREACHABLE_NOTE, EisResolver
from tools.emissions.helpers.inventory.frs_point import FrsLocator
from tools.emissions.helpers.inventory.listing import rank_and_cap
from tools.emissions.helpers.inventory.lookup import lookup_emissions
from tools.emissions.helpers.inventory.plant_hours import PlantHours, get_baseline
from tools.emissions.helpers.inventory.rate import HoursFor, operating_hours_per_year
from tools.emissions.helpers.inventory.tri import TriFetcher
from tools.emissions.helpers.naics_titles import naics_titles, with_titles
from tools.schemas import EmissionRecord, InventoryResult

logger = logging.getLogger(__name__)
Resolve = Callable[[list[EmissionRecord]], list[EmissionRecord]]


def _current_year() -> int:
    """Return the current calendar year (the edge where the clock is read)."""
    return date.today().year


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


def _eis_resolver(client: httpx.Client) -> Resolve:
    """The bulk EIS ID lookup: the shared request policy on the FRS service's own URL."""
    eis = get_frs_eis_settings()
    service = replace(get_efservice_settings(), base_url=eis.base_url)
    return partial(remembered_eis, EisResolver(EfserviceClient(service, client), eis))


def remembered_eis(resolve: Resolve, records: list[EmissionRecord]) -> list[EmissionRecord]:
    """The records with their EIS IDs, asking FRS only for those not remembered."""
    known = {r["frs_id"]: _EIS.get(r["frs_id"]) for r in records}
    unknown = [r for r in records if known[r["frs_id"]] is None]
    for found in resolve(unknown) if unknown else []:
        entry = (found["eis_ids"], found["eis_note"])
        known[found["frs_id"]] = entry
        if found["eis_note"] != UNREACHABLE_NOTE:
            _EIS.put(found["frs_id"], entry)
    out: list[EmissionRecord] = []
    for record in records:
        ids, note = known[record["frs_id"]] or ([], None)
        out.append({**record, "eis_ids": list(ids), "eis_note": note})
    return out


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
        address) and its `frs_id` identifies it. A widely reported chemical
        can take a while because TRI is read in many pages (facilities without TRI coordinates
        are then located in FRS, many per request) and may have over a thousand facilities.
        Only the largest are listed to you, highest `emission_rate` first, so the first
        facilities listed are the largest sources; `total_found`, `matching` and `note` say how
        many more there are. Never present a list as complete when `note` says it is partial.
        To look at a place, call again with `state` and/or `city`: the largest facilities there
        are listed. The listing is a view of the largest sources, not the set to assess: a
        small emitter can matter as much as a large one, and every facility found (listed or
        not) stays available to the assessment. TRI gives
        each facility's primary NAICS code and this tool adds its title in words
        (`naics_title`), nothing about its process; a process is only a candidate derived from
        the industry.
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
          - doc_ctrl_num: TRI control number of that year's submission (null if TRI gave
            none); `fetch_facility_industry` takes it
          - naics_code: primary NAICS code of that submission, digits only (null if TRI gave
            none)
          - eis_ids: the facility's NEI (EIS) facility IDs, looked up for the facilities
            listed; pass them to `fetch_stack_parameters_from_nei` so it needs no lookup of
            its own. Empty when FRS registers no EIS facility for it: then `eis_note` says
            why, and the NEI has no stack for the facility (go to the SCC-based stack)
          - eis_note: null, or why `eis_ids` is empty, or that the IDs are those of another
            FRS record of the same site (TRI's FRS ID had no EIS registration): report that
            with the stacks
          - naics_title: that code's title in words, from the Census code lists (null when
            the code is missing or not a six-digit code of a listed vintage); this is what the
            SCC process search needs. Only when it is null is `fetch_facility_industry`
            worth calling: it asks TRI's own reference table and says whether the facility
            reported the code or EPA assigned it
          - total_release: quantity released in that year, in `unit` per year, as reported
          - unit: unit of `total_release` as reported by TRI, e.g. "Pounds"
          - emission_rate: average emission rate, g/s, assuming the facility operates
            `operating_hours_per_year`
          - operating_hours_per_year: hours per year assumed for `emission_rate`: the
            industry's average plant hours from the Census plant capacity survey when the
            facility's NAICS code (or a shorter prefix of it) is in that survey, otherwise
            8760 (continuous operation, a conservative screening assumption)
          - operating_hours_source: says which of the two it is, and for a survey figure the
            release, the survey's NAICS code and its plant hours per week
          - latitude, longitude: decimal degrees (negative longitude is west); from TRI, or
            from the facility's FRS record when TRI has none
          - address, city, county, state, zip_code: facility location (each may be null)
    """
    return inventory_listing(cas_number, state, city)


Listing = tuple[InventoryResult, list[EmissionRecord]]
_LISTINGS: TtlCache[tuple[str, str | None, str | None, int], Listing] = TtlCache(
    get_assessment_settings().inventory_cache_seconds
)


# FRS ID -> (EIS IDs, note); a lookup FRS could not answer is not remembered.
_EIS: TtlCache[str, tuple[list[str], str | None]] = TtlCache(
    get_frs_eis_settings().cache_seconds, max_entries=50_000
)


def clear_inventory_cache() -> None:
    """Forget every remembered inventory and EIS ID (tests, or a change of configuration)."""
    _LISTINGS.clear()
    _EIS.clear()


def inventory_listing(
    cas_number: str, state: str | None = None, city: str | None = None
) -> Listing:
    """The model's view and the complete matching list of a chemical's inventory.

    The same inventory is reused for ``[assessment].inventory_cache_seconds``, so listing the
    facilities and then assessing them reads TRI once. Copies are returned.
    """
    cas = format_cas(cas_number)
    if cas is None:
        logger.warning("query_emissions_inventory: %r is not a valid CAS number", cas_number)
        return rank_and_cap([], get_tri_settings().max_listed, state, city)
    key = (cas, state, city, _current_year())
    cached = _LISTINGS.get(key)
    if cached is not None:
        return cached
    listing = _read_listing(cas, state, city, key[3])
    _LISTINGS.put(key, listing)
    return listing


def _read_listing(cas: str, state: str | None, city: str | None, year: int) -> Listing:
    """Read TRI (and FRS) for the chemical, then title, rank, cap and resolve the listed."""
    tri = get_tri_settings()
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
            _hours_for(),
        )
        return rank_and_cap(_titled(records), tri.max_listed, state, city, _eis_resolver(client))


def _hours_for() -> HoursFor:
    """The resolver of a facility's operating hours: industry baseline, else the default."""
    settings = get_plant_hours_settings()
    default = operating_hours_per_year(get_emissions_settings())
    return PlantHours(get_baseline(settings), settings, default)


def with_eis_ids(records: list[EmissionRecord]) -> list[EmissionRecord]:
    """Copies of ``records`` with their EIS IDs (for facilities beyond the listed ones)."""
    with _open_client() as client:
        return _eis_resolver(client)(records)


def _titled(records: list[EmissionRecord]) -> list[EmissionRecord]:
    """The records with each NAICS code's title from the local Census code lists."""
    return with_titles(records, naics_titles(get_industry_settings()))
