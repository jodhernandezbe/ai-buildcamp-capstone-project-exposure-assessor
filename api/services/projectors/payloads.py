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


class PropertiesPayload(Payload):
    preferred_name: str | None = None
    molecular_weight: Num | None = None
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
