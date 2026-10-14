"""Typed payloads shared by tool inputs and outputs."""

from __future__ import annotations

from typing import Literal, TypedDict


class ChemicalProperties(TypedDict):
    """Physical-chemical and toxicity values for one chemical."""

    molecular_weight: float  # g/mol
    vapor_pressure: float  # mmHg at 25 C
    rfc: float  # inhalation reference concentration, mg/m3
    iur: float  # inhalation unit risk, (ug/m3)^-1


class PropertyValue(TypedDict):
    """One physical-chemical property value looked up from CompTox."""

    value: float  # in `unit`, exactly as reported by the source
    unit: str  # source unit string, e.g. "mmHg"; never converted
    source: Literal["experimental", "predicted"]  # median type the value came from


class EmissionRecord(TypedDict):
    """One facility's reported emissions of a chemical."""

    frs_id: str
    facility_name: str
    emission_rate: float  # g/s


class StackParameters(TypedDict):
    """Release-point geometry and plume conditions."""

    stack_height: float  # m
    stack_diameter: float  # m
    exit_velocity: float  # m/s
    exit_temperature: float  # K


class FacilityMetadata(TypedDict):
    """Location and classification of a facility."""

    latitude: float  # decimal degrees
    longitude: float  # decimal degrees
    address: str
    scc_code: str


class Meteorology(TypedDict):
    """Representative boundary-layer conditions at a point."""

    wind_speed: float  # m/s
    wind_direction: float  # degrees clockwise from north, direction wind blows from
    stability_class: str  # Pasquill-Gifford class "A" (unstable) to "F" (stable)


class Population(TypedDict):
    """Population living within a search radius."""

    total_population: int
    age_distribution: dict[str, float]  # age band, e.g. "0-4", -> percent of total


class Toxicity(TypedDict):
    """Inhalation toxicity values used for risk characterization."""

    rfc: float  # mg/m3
    iur: float  # (ug/m3)^-1


class ExposureMetrics(TypedDict):
    """Screening-level exposure results."""

    max_concentration: float  # ug/m3, maximum modeled ambient concentration
    add: float  # mg/kg-day, average daily dose
    hq: float  # unitless hazard quotient
