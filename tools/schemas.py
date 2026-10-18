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
    """One facility's most recent reported release of a chemical to one environmental medium."""

    frs_id: str  # EPA Facility Registry Service identifier
    facility_name: str | None
    environmental_medium: str  # TRI medium, e.g. "AIR STACK"
    reporting_year: int  # latest year the facility reported for this medium
    doc_ctrl_num: (
        str | None
    )  # TRI control number of that year's submission (its highest, if several)
    total_release: float  # annual quantity, in `unit`, exactly as reported
    unit: str  # unit of `total_release` as reported, e.g. "Pounds"
    emission_rate: float  # g/s, total_release averaged over `operating_hours_per_year`
    operating_hours_per_year: float  # h/yr assumed for `emission_rate`
    latitude: float  # decimal degrees, positive north
    longitude: float  # decimal degrees, negative west of Greenwich
    address: str | None  # street address
    city: str | None
    county: str | None
    state: str | None  # postal abbreviation, e.g. "TX"
    zip_code: str | None


StackSource = Literal["NEI", "PSTK", "AirToxScreen global default"]


class StackParameters(TypedDict):
    """Release-point geometry and plume conditions.

    The four values are all set or all None (never mixed across sources); ``warnings`` says
    why they are missing or which rule chose them.
    """

    stack_height: float | None  # m above ground
    stack_diameter: float | None  # m
    exit_velocity: float | None  # m/s
    exit_temperature: float | None  # K
    source: StackSource | None  # where the values come from; None when there are none
    scc: str | None  # SCC whose PSTK row supplied the values; None otherwise
    warnings: list[str]


class SccMatch(TypedDict):
    """One SCC whose process description matches an industry description."""

    scc: str  # Source Classification Code, e.g. "30600101"
    level_one: str  # broadest category, e.g. "Industrial Processes"
    level_two: str
    level_three: str
    level_four: str  # most specific process description
    sector: str  # EPA emission sector, e.g. "Industrial Processes - Petroleum Refineries"
    score: float  # semantic similarity, 0 (unrelated) to 1 (identical)


class SccLookupResult(TypedDict):
    """Candidate SCCs for an industry description, best first."""

    matches: list[SccMatch]
    warnings: list[str]


class Meteorology(TypedDict):
    """Representative boundary-layer conditions at a point, for one year.

    The values are annual representatives (not worst-case conditions) from a gridded
    reanalysis; ``source`` says "screening default" when no data could be used.
    """

    wind_speed: float  # m/s, annual mean at 10 m (not below the configured minimum)
    wind_direction: float  # degrees clockwise from north, direction wind blows from
    stability_class: str  # Pasquill-Gifford class "A" (unstable) to "F" (stable)
    ambient_temperature: float  # K, annual mean
    source: str  # data source and year, or "screening default"
    warnings: list[str]  # hours excluded, adjustments made, or why the default was used


class Population(TypedDict):
    """Residents living within a search radius, from census estimates or a labelled default.

    ``source`` is "screening default" when no census data could be used.
    """

    total_population: int  # residents within the radius
    age_distribution: dict[str, float]  # age band "0-4", "5-17", "18-64", "65+" -> percent
    source: str  # data source and vintage, or "screening default"
    warnings: list[str]  # tracts left out, or why the default was used


class Toxicity(TypedDict):
    """Inhalation toxicity values used for risk characterization.

    A value is None when it could not be obtained; the matching risk result is then None.
    """

    rfc: float | None  # mg/m3, inhalation reference concentration
    iur: float | None  # (ug/m3)^-1, inhalation unit risk


class ScenarioResult(TypedDict):
    """The screening result for one set of weather conditions.

    Every number is None when it could not be computed; the result's warnings say why.
    """

    max_concentration: float | None  # ug/m3, annual-average ground-level maximum
    max_concentration_1h: float | None  # ug/m3, 1-hour maximum before the annual factor
    distance_m: float | None  # m, downwind distance of the maximum
    stability_class: str | None  # Pasquill-Gifford class at the maximum
    wind_speed: float | None  # m/s at 10 m, at the maximum
    effective_release_height: float | None  # m, stack height plus plume rise
    hq: float | None  # unitless hazard quotient (annual exposure concentration / RfC)
    cancer_risk: float | None  # unitless lifetime excess cancer risk (exposure concentration x IUR)


class ExposureMetrics(ScenarioResult):
    """Screening-level exposure results for one stack.

    The fields of ``ScenarioResult`` are the EPA SCREEN3-style worst case over a grid of
    weather and distances; ``representative`` is the same for the weather of the meteorology
    input. ``add`` is the highest dose among the age bands present.
    """

    stack_source: str | None  # where the stack came from: "NEI", "PSTK" or the EPA global default
    add: float | None  # mg/(kg*day), average daily dose of the most exposed age band
    add_band: str | None  # age band with the highest dose
    add_by_band: dict[str, float]  # age band present -> dose, mg/(kg*day)
    representative: ScenarioResult  # the result for the representative weather
    warnings: list[str]  # null results, defaults used and the method's limits


class NeiStackResult(TypedDict):
    """Tier 1 stack candidates of a facility, from the NEI.

    ``candidates`` are distinct real stacks (never averaged), lowest stack first, each a
    ``StackParameters`` with source "NEI"; evaluate the exposure for every one.
    """

    eis_ids: list[str]  # NEI facility IDs found for the FRS ID
    candidates: list[StackParameters]  # empty when the NEI has no usable stack
    total_candidates: int  # distinct combinations before the cap
    warnings: list[str]  # why candidates are missing, or what was merged or omitted


class FacilityIndustry(TypedDict):
    """The primary industry of one TRI submission (the one an emission record reports).

    The title (in words) is what the SCC process search needs; the code alone means nothing to
    it. Both are None when no industry could be determined; ``warnings`` says why.
    """

    naics_code: str | None  # six-digit NAICS code, digits only
    naics_title: str | None  # the title of the code, in words
    code_origin: str | None  # "reported" by the facility, "assigned" by EPA, or None if unknown
    source: str | None  # where the industry comes from; None when there is none
    warnings: list[str]  # why a value is missing, or that EPA assigned the code
