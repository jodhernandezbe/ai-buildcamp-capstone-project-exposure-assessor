"""Projector of the batch assessment: every facility's chain, filed like the single tools'.

The artifact holds the assessed facilities (fully, or at their own-stack worst case only) and
the screened-out ones with their screening value; an earlier form was the list of assessed
facilities alone, and is still read.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from api.schemas.workspace import Screening, ScreeningOutcome
from api.services.projectors.ledger import Ledger, Located, Receptor, ToolExchange, text
from api.services.projectors.payloads import (
    AssessedPayload,
    EmissionPayload,
    ScreenedOutPayload,
    validate,
)

_LEFT_OUT = "A facility of the batch assessment was left out: its result was not valid."


def _place(record: EmissionPayload, ledger: Ledger, cas: str | None) -> None:
    ledger.facilities[record.frs_id] = record
    if cas is not None:
        ledger.facility_cas[record.frs_id] = cas


def _site(item: AssessedPayload, ledger: Ledger) -> None:
    """The weather and residents at the facility, when the chain gathered them."""
    record = item.record
    point = (record.latitude, record.longitude)
    if item.meteorology is not None:
        ledger.meteorology.append(Located(*point, item.meteorology))
    if item.population is not None:
        radius = ledger.default_radius_km if item.radius_km is None else item.radius_km
        ledger.population.append(Receptor(Located(*point, item.population), radius))


def _file(item: AssessedPayload, ledger: Ledger, cas: str | None) -> None:
    """One facility's results, keyed so they attach to that facility only."""
    record = item.record
    frs_id = record.frs_id
    _place(record, ledger, cas)
    ledger.nei.append((frs_id, item.stacks))
    for match in item.scc_matches:
        ledger.scc_matches[match.scc] = match
    if item.industry is not None and record.doc_ctrl_num is not None:
        ledger.industries.append((record.doc_ctrl_num, item.industry))
    _site(item, ledger)
    ledger.exposures.append((frs_id, item.exposure))
    outcome: ScreeningOutcome = "full" if item.level == "full" else "worst_case_only"
    bound = item.bound
    ledger.screening[frs_id] = Screening(
        outcome=outcome,
        bound_hq=bound.hq if bound else None,
        bound_cancer_risk=bound.cancer_risk if bound else None,
    )


def _file_out(item: ScreenedOutPayload, ledger: Ledger, cas: str | None) -> None:
    """A screened-out facility: placed, with its own stacks if it has them, and why."""
    frs_id = item.record.frs_id
    _place(item.record, ledger, cas)
    if item.stacks:
        ledger.nei.append((frs_id, item.stacks))
    at_bound = item.stage == "bound"
    ledger.screening[frs_id] = Screening(
        outcome="screened_out_at_bound" if at_bound else "screened_out_with_own_stacks",
        bound_hq=item.hq if at_bound else None,
        bound_cancer_risk=item.cancer_risk if at_bound else None,
        value_hq=item.hq,
        value_cancer_risk=item.cancer_risk,
        reason=item.reason,
    )


def _parts(artifact: object) -> tuple[list[object], list[object]] | None:
    """The assessed and screened-out items; None when the artifact has neither shape."""
    if isinstance(artifact, list):
        return cast(list[object], artifact), []
    if not isinstance(artifact, Mapping):
        return None
    body = cast(Mapping[str, object], artifact)
    assessed, out = body.get("assessed"), body.get("screened_out", [])
    if not isinstance(assessed, list) or not isinstance(out, list):
        return None
    return cast(list[object], assessed), cast(list[object], out)


def project_assessment(exchange: ToolExchange, ledger: Ledger) -> None:
    """Every facility of the call, from the complete artifact (the model's text is a summary)."""
    parts = _parts(exchange.artifact)
    if parts is None:
        ledger.skip(exchange, "it carried no facility details")
        return
    ledger.note_cas(exchange)
    cas = text(exchange.args, "cas_number")
    for raw in parts[0]:
        item = validate(AssessedPayload, raw)
        if item is None:
            ledger.warnings.append(_LEFT_OUT)
        else:
            _file(item, ledger, cas)
    for raw in parts[1]:
        out = validate(ScreenedOutPayload, raw)
        if out is None:
            ledger.warnings.append(_LEFT_OUT)
        else:
            _file_out(out, ledger, cas)
