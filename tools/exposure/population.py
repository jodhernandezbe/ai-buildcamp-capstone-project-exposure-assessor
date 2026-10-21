"""Population receptor lookup tool."""

from __future__ import annotations

import os

import httpx
from langchain_core.tools import tool

from config.population import PopulationSettings, get_population_settings
from tools.credentials import CENSUS_KEY
from tools.exposure.helpers.population.receptors import population_around
from tools.http import RetryingClient
from tools.schemas import Population


def _open_client() -> httpx.Client:
    """Create the HTTP client (the edge where the default collaborator is built)."""
    return httpx.Client()


def _api_key(settings: PopulationSettings) -> str:
    """The Census API key of this request, else the environment's (the edge where it is read)."""
    provided = CENSUS_KEY.get()
    if provided is not None:
        return provided.get_secret_value()
    return os.environ.get(settings.api_key_env_var, "")


@tool
def get_population_receptors(
    latitude: float,
    longitude: float,
    radius_km: float | None = None,
) -> Population:
    """Count the people living around a point and describe their age makeup.

    Purpose:
        Identifies who may be exposed. The result is the `population` input of
        `calculate_exposure_metrics`. Use the facility's latitude and longitude from
        `query_emissions_inventory`. It counts residents (not workers or visitors) from
        U.S. Census ACS 5-year estimates of the census tracts around the point, scaled to the
        circle assuming people are spread evenly over those tracts, so it is a screening
        estimate with sampling error, and it covers the United States only.

    Args:
        latitude: Center latitude, decimal degrees (WGS84), -90 to 90.
        longitude: Center longitude, decimal degrees (WGS84), -180 to 180.
        radius_km: Search radius in kilometers, 0.1 to 50. Omit it for the default of one
            mile (1.609 km).

    Returns:
        A dict with:
        - total_population: number of residents within the radius
        - age_distribution: mapping of age band ("0-4", "5-17", "18-64", "65+") to
          percent of the total population (0.0 to 100.0, summing to 100)
        - source: the data source and vintage, or "screening default" when no census data
          could be used (invalid input, no Census API key, service unreachable, no census
          tract such as open water or a point outside the United States)
        - warnings: tracts left out, or why the screening default was used; if `source` is
          "screening default", say so to the user because the numbers are generic, not
          site-specific
    """
    settings = get_population_settings()
    with _open_client() as http:
        return population_around(
            latitude,
            longitude,
            radius_km,
            settings,
            RetryingClient(settings.policy, http),
            _api_key(settings),
        )
