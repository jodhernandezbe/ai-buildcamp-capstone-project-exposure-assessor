"""The executive summary: chemical, highest risk, selected facility and its context."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial

from api.schemas.workspace import (
    NOT_COMPUTED,
    Chemical,
    ExposureRanges,
    Extreme,
    Extremum,
    Facility,
    ReadAcross,
    RiskSummary,
    Status,
)
from api.services.projectors.ledger import Ledger
from api.services.projectors.payloads import ReadAcrossPayload
from api.services.projectors.rules import WorkspaceRules, cancer_status, hq_status

UNATTRIBUTED_EXPOSURE = "the exposure result could not be matched to one facility"


def _digits(cas: str | None) -> str:
    return "".join(c for c in cas or "" if c.isdigit())


def _read_across(payload: ReadAcrossPayload) -> ReadAcross:
    if payload.is_direct_tri_match:
        kind = "direct_tri_match"
    elif payload.resolution_method == "hybrid_read_across":
        kind = "read_across"
    else:
        kind = "unresolved"
    return ReadAcross(
        kind=kind,
        surrogate_cas=payload.surrogate_tri_cas,
        surrogate_name=payload.surrogate_name,
        hybrid_score=payload.hybrid_read_across_score,
        cosine_similarity=payload.moldeberta_cosine_sim,
        tanimoto_similarity=payload.morgan_tanimoto_sim,
        within_applicability_domain=payload.within_applicability_domain,
        warnings=list(payload.warnings),
    )


def chemical(ledger: Ledger) -> Chemical:
    """The chemical last asked about, with the results that were for that CAS number only."""
    cas = ledger.cas
    result = Chemical(cas_number=cas)
    if ledger.properties and _digits(ledger.properties[0]) == _digits(cas):
        props = ledger.properties[1]
        result = result.model_copy(
            update={
                "molecular_weight_g_mol": props.molecular_weight,
                "rfc_mg_m3": props.rfc,
                "iur_per_ug_m3": props.iur,
                "sources": dict(props.sources),
                "warnings": list(props.warnings),
            }
        )
    if ledger.read_across and _digits(ledger.read_across[0]) == _digits(cas):
        result = result.model_copy(update={"read_across": _read_across(ledger.read_across[1])})
    return result


def _highest(
    facilities: Sequence[Facility],
    entry: Callable[[ExposureRanges], Extreme | None],
    grade: Callable[[float], Status],
) -> Extremum | None:
    best: Extremum | None = None
    for facility in facilities:
        found = entry(facility.exposure) if facility.exposure else None
        if found is not None and (best is None or found.high > best.value):
            best = Extremum(
                value=found.high,
                frs_id=facility.frs_id,
                facility_name=facility.name,
                stack_number=found.high_stack,
                status=grade(found.high),
            )
    return best


def risk_summary(
    facilities: Sequence[Facility], rules: WorkspaceRules, exposure_seen: bool
) -> RiskSummary:
    """The highest worst-case and representative HQ and cancer risk over the facilities."""
    hq = partial(hq_status, thresholds=rules.thresholds)
    risk = partial(cancer_status, thresholds=rules.thresholds)
    summary = RiskSummary(
        hq_worst=_highest(facilities, lambda r: r.hq_worst, hq),
        cancer_risk_worst=_highest(facilities, lambda r: r.cancer_risk_worst, risk),
        hq_representative=_highest(facilities, lambda r: r.hq_representative, hq),
        cancer_risk_representative=_highest(
            facilities, lambda r: r.cancer_risk_representative, risk
        ),
    )
    if any(f.exposure for f in facilities):
        return summary
    return summary.model_copy(
        update={"reason": UNATTRIBUTED_EXPOSURE if exposure_seen else NOT_COMPUTED}
    )


def select(facilities: Sequence[Facility], summary: RiskSummary) -> Facility | None:
    """The facility the ribbon follows: the highest risk one, else the latest with receptors,
    else the only one."""
    leading = summary.hq_worst or summary.cancer_risk_worst
    if leading is not None:
        return next(f for f in facilities if f.frs_id == leading.frs_id)
    with_receptors = [f for f in facilities if f.receptors]
    if with_receptors:
        return with_receptors[-1]
    return facilities[0] if len(facilities) == 1 else None
