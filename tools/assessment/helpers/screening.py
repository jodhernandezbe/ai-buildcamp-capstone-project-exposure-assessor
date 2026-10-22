"""The arithmetic of the tiered screen: worst cases without site weather, bounds and thresholds.

The worst case runs over the SCREEN3 weather combinations, so it needs no site weather, only an
ambient temperature; the screen takes the highest result over the configured temperatures (a
hot day removes the buoyant rise of a cold stack). Concentration, hazard quotient and cancer
risk are linear in the emission rate, so the worst case of the EPA global default stack at
1 g/s, times a facility's rate, bounds every facility from one calculation. The bound assumes a
person at the maximum, so it does not depend on where people live.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.assessment import ScreeningSettings
from tools.assessment.helpers.steps import Steps
from tools.schemas import (
    FacilityExposure,
    Meteorology,
    Population,
    RepresentativeRange,
    ScenarioResult,
    ScreeningBound,
    StackParameters,
    Toxicity,
)

# The representative weather of a screening run is never reported (it would be invented), so
# these values only satisfy the exposure step's contract.
_SCREEN_STABILITY = "D"
_SCREEN_WIND_SPEED = 1.0
_NO_RESIDENTS = Population(
    total_population=0,
    age_distribution={},
    source="not counted (screening worst case)",
    warnings=[],
)


@dataclass(frozen=True)
class Worst:
    """The highest worst case over the screening temperatures, and the result behind it.

    ``exposure`` keeps the worst-case ranges only (the representative ones are emptied).
    """

    hq: float | None
    cancer_risk: float | None
    exposure: FacilityExposure


def _weather(temperature_k: float) -> Meteorology:
    return Meteorology(
        wind_speed=_SCREEN_WIND_SPEED,
        wind_direction=0.0,
        stability_class=_SCREEN_STABILITY,
        ambient_temperature=temperature_k,
        source=f"screening worst case at {temperature_k:g} K (no site weather)",
        warnings=[],
    )


def _high(exposure: FacilityExposure, quantity: str) -> float | None:
    ranges = exposure["range"]
    entry = ranges.get(quantity) if ranges else None
    return entry["high"] if isinstance(entry, dict) else None  # type: ignore[index]


def _without_representative(exposure: FacilityExposure) -> FacilityExposure:
    """The result with the representative case emptied: it came from no real weather."""
    empty = ScenarioResult(
        max_concentration=None,
        max_concentration_1h=None,
        distance_m=None,
        stability_class=None,
        wind_speed=None,
        effective_release_height=None,
        hq=None,
        cancer_risk=None,
    )
    results = [{**r, "representative": empty} for r in exposure["results"]]
    ranges = exposure["range"]
    blank = RepresentativeRange(max_concentration=None, hq=None, cancer_risk=None)
    return {
        **exposure,
        "results": results,  # type: ignore[typeddict-item]
        "range": {**ranges, "representative": blank} if ranges else None,
    }


def worst_case(
    rate: float,
    stacks: list[StackParameters],
    toxicity: Toxicity,
    steps: Steps,
    temperatures: tuple[float, ...],
) -> Worst:
    """The highest worst-case concentration's HQ and cancer risk over the temperatures."""
    runs = [
        steps.exposure(rate, stacks, _weather(t), _NO_RESIDENTS, toxicity) for t in temperatures
    ]
    top = max(runs, key=lambda run: _high(run, "max_concentration") or -1.0)
    return Worst(_high(top, "hq"), _high(top, "cancer_risk"), _without_representative(top))


def unit_bound(steps: Steps, toxicity: Toxicity, temperatures: tuple[float, ...]) -> Worst:
    """The worst case of the EPA global default stack at 1 g/s."""
    return worst_case(1.0, [steps.pstk(None)], toxicity, steps, temperatures)


def scaled(unit: Worst, rate: float) -> ScreeningBound:
    """A facility's bound: the unit-rate worst case times its emission rate (g/s)."""
    return ScreeningBound(
        hq=None if unit.hq is None else unit.hq * rate,
        cancer_risk=None if unit.cancer_risk is None else unit.cancer_risk * rate,
    )


def can_screen(unit: Worst) -> bool:
    """Whether any benchmark gave a value: without one nothing can be screened out."""
    return unit.hq is not None or unit.cancer_risk is not None


def exceedance(hq: float | None, risk: float | None, thresholds: ScreeningSettings) -> float:
    """The larger of HQ / its threshold and risk / its threshold; -1 when neither is known."""
    ratios = [
        value / limit
        for value, limit in ((hq, thresholds.hq), (risk, thresholds.cancer_risk))
        if value is not None
    ]
    return max(ratios, default=-1.0)


def reaches(hq: float | None, risk: float | None, thresholds: ScreeningSettings) -> bool:
    """Whether either value is at or above its threshold."""
    return exceedance(hq, risk, thresholds) >= 1.0
