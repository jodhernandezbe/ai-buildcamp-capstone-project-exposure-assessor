"""Workspace contract: everything the left pane shows, built only from tool results.

Every number here was reported by a tool (or is a maximum of such numbers); a quantity no tool
reported is ``None``. Units are in the field descriptions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.base import ContractModel

Status = Literal["below", "near", "above"]
Tier = Literal[1, 2, 3]
ProvenanceKind = Literal["not_evaluated", "direct_tri_match", "read_across", "unresolved"]
NOT_COMPUTED = "not yet computed"


class Scenario(ContractModel):
    """Screening result for one set of weather: concentration µg/m³, HQ and cancer risk unitless."""

    max_concentration_ug_m3: float | None = None
    distance_m: float | None = Field(default=None, description="Downwind distance of the maximum.")
    hq: float | None = None
    cancer_risk: float | None = None


class Stack(ContractModel):
    """One release point with its provenance tier and, when computed, its results.

    Attributes:
        stack_number: 1-based position in the exposure call that evaluated it, else None.
        tier: 1 Empirical NEI, 2 PSTK by SCC, 3 EPA global default; None without a source.
        tier_label: ``Tier 1: Empirical NEI`` and so on.
        scc: SCC behind a PSTK stack, when reported.
        scc_description: Most specific process description of that SCC, from an SCC lookup
            in the same thread; None when no lookup returned it.
        scc_score: Match score (0-1) of that lookup.
    """

    stack_number: int | None = None
    height_m: float | None = None
    diameter_m: float | None = None
    exit_velocity_m_s: float | None = None
    exit_temperature_k: float | None = None
    source: str | None = None
    tier: Tier | None = None
    tier_label: str | None = None
    scc: str | None = None
    scc_description: str | None = None
    scc_score: float | None = None
    worst_case: Scenario | None = None
    representative: Scenario | None = None
    warnings: list[str] = Field(default_factory=list[str])


class Extreme(ContractModel):
    """The lowest and highest value of one quantity over a facility's stacks."""

    low: float
    high: float
    low_stack: int
    high_stack: int


class ExposureRanges(ContractModel):
    """Ranges over the evaluated stacks of one facility; None when no stack has the quantity."""

    stacks_given: int
    stacks_evaluated: int
    hq_worst: Extreme | None = None
    cancer_risk_worst: Extreme | None = None
    concentration_worst: Extreme | None = None
    hq_representative: Extreme | None = None
    cancer_risk_representative: Extreme | None = None
    concentration_representative: Extreme | None = None
    warnings: list[str] = Field(default_factory=list[str])


class Industry(ContractModel):
    """Primary industry of the TRI submission; origin is reported, assigned or None."""

    naics_code: str | None = None
    naics_title: str | None = None
    code_origin: str | None = None
    source: str | None = None


class Receptors(ContractModel):
    """Residents within ``radius_km`` of a point; ``age_distribution`` is percent per band."""

    total_population: int
    radius_km: float
    age_distribution: dict[str, float]
    source: str
    screening_default: bool
    warnings: list[str] = Field(default_factory=list[str])


class Meteorology(ContractModel):
    """Annual representative conditions at a point: m/s, degrees clockwise from north, K."""

    wind_speed_m_s: float
    wind_from_deg: float = Field(description="Direction the wind blows from.")
    wind_toward_deg: float = Field(description="Downwind direction, ``(from + 180) % 360``.")
    ambient_temperature_k: float
    stability_class: str
    source: str
    screening_default: bool
    warnings: list[str] = Field(default_factory=list[str])


class Polygon(ContractModel):
    """A GeoJSON polygon: one closed ring of ``[longitude, latitude]`` positions (WGS84)."""

    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]


class Facility(ContractModel):
    """One facility of the emissions inventory with what the other tools reported about it.

    Attributes:
        doc_ctrl_num: TRI document control number (the inventory has no TRI facility ID).
        total_release: Annual quantity in ``release_unit``, as reported.
        emission_rate_g_s: Total release averaged over ``operating_hours_per_year``.
        stack_source: Where the NEI stack lookup came from, when one was made for the facility.
        status: Worst-case risk status; None while no risk is computed.
        buffer: The receptor radius drawn as a circle around the facility, when receptors exist.
        sector: Schematic downwind sector (toward ``wind_toward_deg``, length the receptor radius);
            never a modelled plume footprint. Present with both receptors and meteorology.
    """

    frs_id: str
    name: str | None = None
    address: str | None = None
    city: str | None = None
    county: str | None = None
    state: str | None = None
    zip_code: str | None = None
    latitude: float
    longitude: float
    cas_number: str | None = None
    doc_ctrl_num: str | None = None
    medium: str
    reporting_year: int
    total_release: float
    release_unit: str
    emission_rate_g_s: float
    operating_hours_per_year: float
    industry: Industry | None = None
    stacks: list[Stack] = Field(default_factory=list[Stack])
    receptors: Receptors | None = None
    meteorology: Meteorology | None = None
    exposure: ExposureRanges | None = None
    status: Status | None = None
    buffer: Polygon | None = None
    sector: Polygon | None = None


class Extremum(ContractModel):
    """The highest value of one risk quantity over every attributed facility.

    Attributes:
        value: The value (HQ and cancer risk are unitless).
        frs_id: Facility whose stack gave it.
        facility_name: That facility's name, as reported.
        stack_number: The stack that gave it.
        status: Position against the configured thresholds of concern.
    """

    value: float
    frs_id: str
    facility_name: str | None = None
    stack_number: int
    status: Status


class RiskSummary(ContractModel):
    """Highest worst-case and representative HQ and cancer risk; ``reason`` when none exists."""

    hq_worst: Extremum | None = None
    cancer_risk_worst: Extremum | None = None
    hq_representative: Extremum | None = None
    cancer_risk_representative: Extremum | None = None
    reason: str | None = Field(default=None, description="Why no value yet, e.g. not computed.")


class ReadAcross(ContractModel):
    """The read-across outcome for the queried chemical (surrogate values are scores 0-1)."""

    kind: ProvenanceKind = "not_evaluated"
    surrogate_cas: str | None = None
    surrogate_name: str | None = None
    hybrid_score: float | None = None
    cosine_similarity: float | None = None
    tanimoto_similarity: float | None = None
    within_applicability_domain: bool | None = None
    warnings: list[str] = Field(default_factory=list[str])


class Chemical(ContractModel):
    """The chemical as queried, with its properties and read-across provenance.

    Attributes:
        cas_number: CAS number as queried.
        molecular_weight_g_mol: Molecular weight, g/mol.
        rfc_mg_m3: Inhalation reference concentration, mg/m³.
        iur_per_ug_m3: Inhalation unit risk, (µg/m³)⁻¹.
        sources: Field name -> source the value came from.
    """

    cas_number: str | None = None
    molecular_weight_g_mol: float | None = None
    rfc_mg_m3: float | None = None
    iur_per_ug_m3: float | None = None
    sources: dict[str, str] = Field(default_factory=dict[str, str])
    read_across: ReadAcross = Field(default_factory=ReadAcross)
    warnings: list[str] = Field(default_factory=list[str])


class Unattributed(ContractModel):
    """A result that could not be tied to exactly one facility, and why."""

    tool: str
    reason: str


class BoundingBox(ContractModel):
    """Extent of the placed facilities and buffers, decimal degrees (WGS84)."""

    west: float
    south: float
    east: float
    north: float


class WorkspaceState(ContractModel):
    """The current workspace of one thread.

    Attributes:
        framing_version: Increases only when the set of placed facilities or buffers changes.
        bounds: Extent of the placed facilities and buffers; None when none is placed.
        facilities: One per FRS ID, in the order first reported.
        selected_frs_id: Facility whose receptors the ribbon shows (the highest risk, or the
            only one); None when no single facility stands out.
        chemical: The queried chemical and its provenance.
        risk: Highest risk values across the attributed facilities.
        receptors: Receptors of the selected facility.
        meteorology: Meteorology of the selected facility, else the latest result.
        unattributed: Results not attached to any facility.
        warnings: Results left out (malformed, unattributable) and why.
    """

    framing_version: int = Field(default=0, ge=0)
    bounds: BoundingBox | None = None
    facilities: list[Facility] = Field(default_factory=list[Facility])
    selected_frs_id: str | None = None
    chemical: Chemical = Field(default_factory=Chemical)
    risk: RiskSummary = Field(default_factory=RiskSummary)
    receptors: Receptors | None = None
    meteorology: Meteorology | None = None
    unattributed: list[Unattributed] = Field(default_factory=list[Unattributed])
    warnings: list[str] = Field(default_factory=list[str])
