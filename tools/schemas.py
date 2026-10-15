"""Typed payloads shared by tool inputs and outputs."""

from __future__ import annotations

from typing import Literal, TypedDict


class ChemicalProperties(TypedDict):
    """Physical-chemical and toxicity values for one chemical, in the units noted below.

    A value is None when it could not be obtained or converted; ``warnings`` says why.
    """

    molecular_weight: float | None  # g/mol
    vapor_pressure: float | None  # mmHg, as reported by the source (typically 25 C)
    density: float | None  # g/cm^3
    rfd: float | None  # oral reference dose, mg/(kg*day)
    rfc: float | None  # inhalation reference concentration, mg/m^3
    sf: float | None  # oral cancer slope factor, (mg/(kg*day))^-1
    iur: float | None  # inhalation unit risk, (ug/m^3)^-1
    sources: dict[str, str]  # field -> "CompTox", "experimental", "predicted" or ToxVal source
    toxicity_details: dict[str, ToxicityDetail]  # rfd/rfc/sf/iur found -> route and endpoint
    warnings: list[str]  # one entry per missing or unconvertible value


class PropertyValue(TypedDict):
    """One physical-chemical property value looked up from CompTox."""

    value: float  # in `unit`, exactly as reported by the source
    unit: str  # source unit string, e.g. "mmHg"; never converted
    source: Literal["experimental", "predicted"]  # median type the value came from


class ToxicityValue(TypedDict):
    """One toxicity value (RfD, RfC, SF, IUR, ...) looked up from CompTox ToxVal."""

    value: float  # in `unit`, exactly as reported by the source
    unit: str  # source unit string, e.g. "mg/kg-day"; never converted
    source: str  # ToxVal source database name for the chosen record
    route: str  # exposure route as recorded on the chosen record, lower-case, e.g. "oral"
    endpoint: str | None  # critical effect or cancer endpoint, e.g. "leukemia"; None if unstated
    assessment: str | None  # "cancer" or "non-cancer" as recorded; None if unstated


class ToxicityDetail(TypedDict):
    """Context of one toxicity value, for explaining it to the user."""

    source: str  # database the value comes from, e.g. "IRIS"
    exposure_route: str  # route the value applies to: "oral" or "inhalation"
    route_reported: str  # route as recorded by the source; "not specified" if it gave none
    endpoint: str | None  # critical effect or cancer endpoint, e.g. "leukemia"; None if unstated
    assessment: str | None  # "cancer" or "non-cancer"; None if unstated


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
