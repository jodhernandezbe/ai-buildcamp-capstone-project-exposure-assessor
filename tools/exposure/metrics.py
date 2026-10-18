"""Exposure metric tool."""

from __future__ import annotations

from langchain_core.tools import tool

from config.exposure import get_exposure_settings
from tools.exposure.helpers.assessment import assess_exposure
from tools.schemas import ExposureMetrics, Meteorology, Population, StackParameters, Toxicity


@tool
def calculate_exposure_metrics(
    emission_rate: float,
    stack_params: StackParameters,
    meteorology: Meteorology,
    population: Population,
    toxicity: Toxicity,
) -> ExposureMetrics:
    """Compute screening-level air concentration, dose and health risk for one stack.

    Purpose:
        Use this once the source, the release geometry, the weather, the people and the
        toxicity benchmarks are known, to learn how much of the chemical people may breathe
        and how that compares with health benchmarks. It evaluates ONE stack: when a facility
        has several candidate stacks (or you are unsure which stack applies), call it once
        per stack and report the range. It does not look anything up; every input comes from
        the other tools, exactly as they returned it.

    Method:
        The U.S. EPA SCREEN3 screening procedure, flat terrain, rural dispersion, no building
        downwash, no mixing-height limit, one source, no deposition or chemistry. The WORST
        CASE is the highest ground-level centerline concentration over EPA's 54 combinations
        of stability class and 10 m wind speed and over distances from 100 m to 10 km; the
        REPRESENTATIVE case uses only the weather you pass in. The 1-hour maximum is turned
        into an annual average with EPA's screening factor before it is compared with chronic
        benchmarks. The worst case may fall where nobody lives; it is a screening bound, not
        a prediction for a place.

    Args:
        emission_rate: Source emission rate, g/s (the `emission_rate` of the emissions
            inventory).
        stack_params: One stack with `stack_height` (m), `stack_diameter` (m), `exit_velocity`
            (m/s) and `exit_temperature` (K): one entry of the NEI candidates, or the result
            of the SCC-based (generic) stack source. If a value is null the stack cannot be
            used.
        meteorology: The meteorology result: 10 m `wind_speed` (m/s), `stability_class`,
            `ambient_temperature` (K), with its `source`.
        population: The population result: `age_distribution` (percent per age band) with its
            `source`. It selects which age bands get a dose.
        toxicity: `rfc` (mg/m3) and `iur` ((ug/m3)^-1) from the chemical properties; either
            may be null, and the matching risk is then null.

    Returns:
        A dict with, for the WORST CASE:
        - max_concentration: annual-average ground-level concentration at the maximum, ug/m3
        - max_concentration_1h: the 1-hour maximum, ug/m3
        - distance_m, stability_class, wind_speed (10 m, m/s), effective_release_height (m):
          where and under which weather the maximum occurs
        - hq: hazard quotient (annual exposure concentration / RfC); above 1 means the
          exposure exceeds the non-cancer benchmark
        - cancer_risk: lifetime excess cancer risk (exposure concentration x IUR); 1e-6 is one
          in a million
        - add: average daily dose of the most exposed age band, mg/(kg*day); add_band names
          it and add_by_band gives every band that has residents. Doses differ by age
          (children breathe more per kg); hq and cancer_risk do not, because the RfC and IUR
          are concentration-based.
        and `representative`, a dict with the same concentration, distance, class, wind,
        height, hq and cancer_risk fields for the representative weather (it does not exceed
        the worst case), and `warnings`.
        A null number means it could not be computed, and `warnings` says why (missing stack
        value, missing RfC or IUR, invalid input); nothing is ever defaulted or guessed, so a
        null must be reported, not filled in. `stack_source` echoes where the stack came from;
        a stack that is the EPA global default or a process default is generic (short, cold
        and slow), so concentrations, hq and cancer_risk can be far higher than for the
        facility's real stack: report that with the numbers. `warnings` also say when the weather or
        the population input was itself a generic default, when the maximum is at the edge of the
        range, and that the worst case may be where nobody lives; pass these on.
        These are screening estimates, not regulatory determinations.
    """
    return assess_exposure(
        emission_rate, stack_params, meteorology, population, toxicity, get_exposure_settings()
    )
