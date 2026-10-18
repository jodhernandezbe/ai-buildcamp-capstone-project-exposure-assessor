"""Compose paged retrieval and row reduction into one emissions lookup."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from config.loader import EmissionsSettings, TriSettings
from tools.emissions.helpers.efservice import EfserviceError
from tools.emissions.helpers.inventory.reduce import LatestReports
from tools.emissions.helpers.inventory.tri import TriFetcher
from tools.schemas import EmissionRecord

logger = logging.getLogger(__name__)


def lookup_emissions(
    cas: str,
    tri: TriSettings,
    emissions: EmissionsSettings,
    aliases: Mapping[str, str] | None,
    fetcher: TriFetcher,
) -> list[EmissionRecord]:
    """Find the latest-year release record of each facility for a chemical.

    Args:
        cas: Hyphenated CAS registry number, already validated.
        tri: TRI settings (media to keep, column names).
        emissions: Emission-rate assumptions.
        aliases: Source unit spelling -> Pint-parsable unit string.
        fetcher: Source of TRI rows (injected).

    Returns:
        One record per (medium, facility); empty if nothing was reported or if retrieval
        failed (a partial result is never returned as if it were complete). Data problems
        and a hit page cap are logged as warnings.
    """
    reducer = LatestReports(tri)
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
    records = reducer.records(emissions, aliases)
    for message in reducer.stats.warnings():
        logger.warning("TRI %s: %s", cas, message)
    return records
