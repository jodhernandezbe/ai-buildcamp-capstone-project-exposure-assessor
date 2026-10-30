"""Strict models of the tool results the workspace reads (external data is untrusted).

Each model lists only the fields the workspace uses; ``tests/api/services/projectors`` check
that every one of them still exists in the tool's result type, so a renamed field fails loudly.
Numbers must be finite and never ``bool``.
"""

from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

Num = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Lat = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-90, le=90)]
Lon = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=-180, le=180)]


class Payload(BaseModel):
    """Base of the payload models: strict types, unknown fields ignored."""

    model_config = ConfigDict(strict=True, extra="ignore", frozen=True)


class ConditionPayload(Payload):
    tri_activity: str
    tri_section: str
    lifecycle_stage: str
    cou_category: str
    mapping_strength: str


class EmissionPayload(Payload):
    frs_id: str
    facility_name: str | None = None
    environmental_medium: str
    reporting_year: int
    doc_ctrl_num: str | None = None
    naics_code: str | None = None
    naics_title: str | None = None
    naics_subsector: str | None = None
    naics_subsector_title: str | None = None
    eis_ids: list[str] = []
    eis_note: str | None = None
    total_release: Num
    unit: str
    emission_rate: Num
    operating_hours_per_year: Num
    operating_hours_source: str | None = None
    fugitive_release_kg_per_year: Num | None = None
    fugitive_reporting_year: int | None = None
    conditions_of_use: list[ConditionPayload] = []
    lifecycle_stages: list[str] = []
    conditions_note: str | None = None
    latitude: Lat
    longitude: Lon
    address: str | None = None
    city: str | None = None
    county: str | None = None
    state: str | None = None
    zip_code: str | None = None


Tier = Literal["exceedance", "elevated", "acceptable"]


class VentilationTierPayload(Payload):
    label: str
    ventilation_m3_per_s: Num
    mixing_factor: Num
    workplace_concentration_mg_m3: Num | None = None
    twa_mg_m3: Num | None = None
    oel_ratio: Num | None = None
    hq: Num | None = None
    cancer_risk: Num | None = None
    risk_tier: Tier | None = None


class OccupationalPayload(Payload):
    """The worker screening of one facility, as the assessment tool returned it."""

    fugitive_release_kg_per_year: Num | None = None
    fugitive_reporting_year: int | None = None
    operating_days_per_year: Num | None = None
    hours_per_day: Num | None = None
    oel_twa_mg_m3: Num | None = None
    oel_source: str | None = None
    rfc: Num | None = None
    iur: Num | None = None
    vapor_pressure_mmhg: Num | None = None
    vapor_pressure_source: str | None = None
    baseline: VentilationTierPayload
    worst_case: VentilationTierPayload
    risk_tier: Tier | None = None
    assumptions: list[str] = Field(default_factory=list[str])
    warnings: list[str] = Field(default_factory=list[str])


class CdrSectorPayload(Payload):
    code: str
    name: str
    matched_naics_prefix: str
    naics_edition: str


class ProfilePayload(Payload):
    """The operational profile of one facility, as the assessment tool returned it."""

    naics_code: str | None = None
    life_cycle_stage: list[str] = Field(default_factory=list[str])
    cou_category: list[str] = Field(default_factory=list[str])
    cdr_sector: CdrSectorPayload | None = None
    days_per_week: int | None = None
    operating_days_per_year: Num | None = None
    hours_per_day: Num | None = None
    annual_operating_hours: Num | None = None
    schedule_source: str | None = None
    warnings: list[str] = Field(default_factory=list[str])


class IndustryPayload(Payload):
    naics_code: str | None = None
    naics_title: str | None = None
    code_origin: str | None = None
    source: str | None = None


class StackPayload(Payload):
    stack_height: Num | None = None
    stack_diameter: Num | None = None
    exit_velocity: Num | None = None
    exit_temperature: Num | None = None
    source: str | None = None
    scc: str | None = None
    warnings: list[str] = Field(default_factory=list[str])


class NeiPayload(Payload):
    candidates: list[StackPayload]
    warnings: list[str] = Field(default_factory=list[str])


class SccMatchPayload(Payload):
    scc: str
    level_four: str
    score: Num


class SccLookupPayload(Payload):
    matches: list[SccMatchPayload]


class LimitsPayload(Payload):
    oel_twa_mg_m3: Num | None = None
    oel_source: str | None = None


class PropertiesPayload(Payload):
    preferred_name: str | None = None
    molecular_weight: Num | None = None
    vapor_pressure: Num | None = None
    density: Num | None = None
    occupational_limits: LimitsPayload | None = None
    rfc: Num | None = None
    iur: Num | None = None
    sources: dict[str, str] = Field(default_factory=dict[str, str])
    warnings: list[str] = Field(default_factory=list[str])


class ReadAcrossPayload(Payload):
    query_cas: str
    is_direct_tri_match: bool
    surrogate_tri_cas: str | None = None
    surrogate_name: str | None = None
    moldeberta_cosine_sim: Num | None = None
    morgan_tanimoto_sim: Num | None = None
    hybrid_read_across_score: Num | None = None
    within_applicability_domain: bool
    resolution_method: str
    warnings: list[str] = Field(default_factory=list[str])


class MeteorologyPayload(Payload):
    wind_speed: Num
    wind_direction: Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0, le=360)]
    stability_class: str
    ambient_temperature: Num
    source: str
    warnings: list[str] = Field(default_factory=list[str])


class PopulationPayload(Payload):
    total_population: int
    age_distribution: dict[str, Num]
    source: str
    warnings: list[str] = Field(default_factory=list[str])


class ScenarioPayload(Payload):
    max_concentration: Num | None = None
    distance_m: Num | None = None
    hq: Num | None = None
    cancer_risk: Num | None = None


class StackExposurePayload(ScenarioPayload):
    stack_number: int
    stack_height: Num | None = None
    stack_diameter: Num | None = None
    exit_velocity: Num | None = None
    exit_temperature: Num | None = None
    stack_source: str | None = None
    add: Num | None = None
    add_band: str | None = None
    add_by_band: dict[str, Num] = Field(default_factory=dict[str, Num])
    representative: ScenarioPayload
    warnings: list[str] = Field(default_factory=list[str])


class RangeEntryPayload(Payload):
    low: Num
    high: Num
    low_stack: int
    high_stack: int


class RepresentativeRangePayload(Payload):
    max_concentration: RangeEntryPayload | None = None
    hq: RangeEntryPayload | None = None
    cancer_risk: RangeEntryPayload | None = None


class ExposureRangePayload(Payload):
    max_concentration: RangeEntryPayload | None = None
    hq: RangeEntryPayload | None = None
    cancer_risk: RangeEntryPayload | None = None
    representative: RepresentativeRangePayload


class ExposurePayload(Payload):
    results: list[StackExposurePayload]
    range: ExposureRangePayload | None = None
    stacks_given: int
    stacks_evaluated: int
    warnings: list[str] = Field(default_factory=list[str])


class BoundPayload(Payload):
    hq: Num | None = None
    cancer_risk: Num | None = None


class ScenarioFactorPayload(Payload):
    key: str
    group: Literal["source", "release", "conditions", "receptor_model"]
    label: str
    value: Num | str | None = None
    unit: str = ""
    source: str | None = None
    reason: str | None = None


class ScenarioReceptorPayload(Payload):
    kind: Literal["tract", "workers"]
    label: str
    residents: int | None = None
    age_distribution: dict[str, Num] = Field(default_factory=dict[str, Num])
    distance_m: Num | None = None
    bearing_deg: Num | None = None
    latitude: Num | None = None
    longitude: Num | None = None
    concentration: Num | None = None
    fraction_of_maximum: Num | None = None
    note: str | None = None


class WorstCaseScenarioPayload(Payload):
    """One worst-case scenario of a facility, as the assessment tool returned it."""

    pathway_key: str
    pathway: str
    quantity: str
    quantity_label: str
    value: Num
    tier: str | None = None
    benchmark: Num | None = None
    factors: list[ScenarioFactorPayload] = Field(default_factory=list[ScenarioFactorPayload])
    receptors: list[ScenarioReceptorPayload] = Field(default_factory=list[ScenarioReceptorPayload])
    receptors_note: str | None = None
    notes: list[str] = Field(default_factory=list[str])


class AssessedPayload(Payload):
    """One facility of the batch assessment: its record and every result of its chain.

    At "worst case only" it has no weather or residents (they were not requested).
    """

    record: EmissionPayload
    level: Literal["full", "worst case only"] = "full"
    bound: BoundPayload | None = None
    stacks: list[StackPayload]
    scc_matches: list[SccMatchPayload] = Field(default_factory=list[SccMatchPayload])
    industry: IndustryPayload | None = None
    meteorology: MeteorologyPayload | None = None
    population: PopulationPayload | None = None
    radius_km: Num | None = None
    exposure: ExposurePayload
    # Validated on their own, so an invalid one leaves out only itself, with a warning.
    occupational_exposure: object = None
    operational_profile: object = None
    scenarios: list[object] = Field(default_factory=list[object])


class ScreenedOutPayload(Payload):
    """A facility the batch assessment left out, with its screening value and the reason."""

    record: EmissionPayload
    stage: Literal["bound", "own stacks"]
    hq: Num | None = None
    cancer_risk: Num | None = None
    stacks: list[StackPayload] = Field(default_factory=list[StackPayload])
    reason: str


class NotAssessedPayload(Payload):
    """A facility the batch assessment did not assess, and why."""

    frs_id: str
    reason: str


def decode_json(content: object) -> object | None:
    """The JSON value of a tool message's text; None when it is not valid JSON text."""
    if not isinstance(content, str):
        return None
    try:
        return json.loads(content)
    except ValueError:
        return None


def validate[T](model: type[T], value: object) -> T | None:
    """The value as ``model`` when it has the right shape, else None."""
    try:
        return TypeAdapter(model).validate_python(value)
    except ValidationError:
        return None
