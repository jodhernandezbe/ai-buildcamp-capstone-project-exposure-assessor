"""Meteorology lookup tool."""

from __future__ import annotations

from datetime import date

import httpx
from langchain_core.tools import tool

from config.loader import get_unit_settings
from config.meteorology import get_meteorology_settings
from tools.exposure.helpers.conditions import meteorology_for
from tools.http import RetryingClient
from tools.schemas import Meteorology


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


def _today() -> date:
    """Return today's date (the edge where the clock is read)."""
    return date.today()


@tool
def get_meteorological_boundary(
    latitude: float,
    longitude: float,
    reporting_year: int | None = None,
) -> Meteorology:
    """Get representative meteorological conditions for dispersion modeling at a point.

    Purpose:
        Supplies the wind and atmospheric stability inputs of the transport model used by
        `calculate_exposure_metrics`. Use the facility's latitude and longitude from
        `query_emissions_inventory`. The values summarize one year of hourly reanalysis
        (ERA5, a grid of about 25 km, not a nearby weather station): they are annual
        representatives, not worst-case conditions, and local effects such as terrain or
        sea breezes are not captured. Wind is at 10 m, not at stack height.

    Args:
        latitude: Decimal degrees (WGS84), positive north, -90 to 90.
        longitude: Decimal degrees (WGS84), positive east, -180 to 180.
        reporting_year: Calendar year of the hourly data. Omit it for the configured
            default; it must be a complete year the archive covers.

    Returns:
        A dict with:
        - wind_speed: m/s, annual mean (not below a configured minimum)
        - wind_direction: degrees clockwise from north, the direction the wind blows from
          (centre of the most frequent 10 degree sector)
        - stability_class: most frequent hourly Pasquill-Gifford class, "A" (very unstable)
          to "F" (stable)
        - ambient_temperature: K, annual mean
        - source: the data source and year, or "screening default" when no data could be
          used (invalid input, archive unreachable, no usable hours)
        - warnings: hours left out, adjustments made, or why the screening default was
          used; if `source` is "screening default", say so to the user because the values
          are generic, not site-specific
    """
    settings = get_meteorology_settings()
    with _open_client() as http:
        return meteorology_for(
            latitude,
            longitude,
            reporting_year,
            settings,
            RetryingClient(settings.policy, http),
            get_unit_settings().aliases,
            _today(),
        )
