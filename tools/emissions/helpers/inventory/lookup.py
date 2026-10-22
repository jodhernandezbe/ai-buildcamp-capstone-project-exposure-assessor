"""Compose paged retrieval and row reduction into one emissions lookup."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from config.loader import EmissionsSettings, TriSettings
from tools.emissions.helpers.efservice import EfserviceError
from tools.emissions.helpers.inventory.rate import HoursFor
from tools.emissions.helpers.inventory.reduce import LatestReports, Locator
from tools.emissions.helpers.inventory.tri import TriFetcher
from tools.schemas import EmissionRecord

logger = logging.getLogger(__name__)


def lookup_emissions(
    cas: str,
    tri: TriSettings,
    emissions: EmissionsSettings,
    aliases: Mapping[str, str] | None,
    fetcher: TriFetcher,
    current_year: int,
    locate: Locator | None = None,
    hours_for: HoursFor | None = None,
) -> list[EmissionRecord]:
    """Find the latest-year release record of each facility for a chemical.

    Args:
        cas: Hyphenated CAS registry number, already validated.
        tri: TRI settings (media to keep, column names).
        emissions: Emission-rate assumptions.
        aliases: Source unit spelling -> Pint-parsable unit string.
        fetcher: Source of TRI rows (injected).
        current_year: The current calendar year; only the last ``tri.recent_years`` reporting
            years ending with it are used.
        locate: Gives the coordinates of many facilities from their FRS IDs in one call
            (injected); used only for facilities whose TRI rows have none. Without it such
            facilities are omitted.
        hours_for: Gives a facility's operating hours from its NAICS code (injected); without it
            every facility gets the default hours of ``emissions``.

    Returns:
        One record per (medium, facility); empty if nothing was reported or if retrieval
        failed (a partial result is never returned as if it were complete). Data problems
        and a hit page cap are logged as warnings.
    """
    reducer = LatestReports(tri, tri.first_year(current_year))
    try:
        for medium in tri.media:
            if fetcher.fetch(cas, medium, reducer.add_rows):
                logger.warning(
                    "TRI %s %s: page cap (%d pages) reached; the result may be incomplete",
                    cas,
                    medium,
                    tri.max_pages,
                )
    except EfserviceError as exc:
        logger.warning("TRI emissions lookup for %s failed: %s", cas, exc)
        return []
    records = reducer.records(emissions, aliases, locate, hours_for)
    for message in reducer.stats.warnings():
        logger.warning("TRI %s: %s", cas, message)
    return records
