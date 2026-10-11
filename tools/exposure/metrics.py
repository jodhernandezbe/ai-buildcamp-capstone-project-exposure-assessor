"""Population and exposure metric tools."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import ExposureMetrics, Meteorology, Population, StackParameters, Toxicity


@tool
def get_population_receptors(latitude: float, longitude: float, radius_km: float) -> Population:
    """Count the people living around a point and describe their age makeup.

    Purpose:
        Identifies who may be exposed. The result is the `population` input of
        `calculate_exposure_metrics`.

    Args:
        latitude: Center latitude, decimal degrees (WGS84).
        longitude: Center longitude, decimal degrees (WGS84).
        radius_km: Search radius in kilometers.

    Returns:
        A dict with:
        - total_population: number of residents within the radius
        - age_distribution: mapping of age band (e.g. "0-4", "65+") to percent of
          the total population
    """
    raise NotImplementedError


@tool
def calculate_exposure_metrics(
    emission_rate: float,
    stack_params: StackParameters,
    meteorology: Meteorology,
    population: Population,
    toxicity: Toxicity,
) -> ExposureMetrics:
    """Compute screening-level exposure and risk metrics from a point source.

    Purpose:
        Final step of an assessment: runs a dispersion model for the source,
        converts the concentration to a dose for the receptor population, and
        compares it to toxicity benchmarks. Results are screening estimates, not
        regulatory determinations.

    Args:
        emission_rate: Source emission rate, g/s (from `query_emissions_inventory`).
        stack_params: Output of `fetch_stack_parameters`.
        meteorology: Output of `get_meteorological_boundary`.
        population: Output of `get_population_receptors`.
        toxicity: Dict with `rfc` (mg/m3) and `iur` (per ug/m3), taken from
            `fetch_chemical_properties`.

    Returns:
        A dict with:
        - max_concentration: maximum modeled ambient concentration, ug/m3
        - add: average daily dose, mg/kg-day
        - hq: hazard quotient (concentration / RfC); values above 1 flag potential concern
    """
    raise NotImplementedError
