"""The values the user supplied for missing benchmarks, shown on the chemical as theirs."""

from __future__ import annotations

from collections.abc import Mapping

from api.services.projectors.ledger import Ledger
from api.services.projectors.payloads import LimitsPayload, PropertiesPayload

USER_PROVIDED = "user-provided"
# The PropertiesPayload fields a missing value can fill, and the occupational limit (nested).
_FIELDS = ("rfc", "iur", "molecular_weight", "vapor_pressure", "density")
_LIMIT = "oel_twa"


def apply_supplied(ledger: Ledger, supplied: Mapping[str, float]) -> None:
    """Fill the chemical's empty benchmarks with the values the user supplied, labelled as theirs.

    Keys are entry IDs such as ``rfc:71-43-2``. A value is only set where the chemical has none,
    and only for the CAS number the thread is about (or the first one, when none is known yet).
    The value is in the target unit the entry asked for, so it is shown as given.
    """
    for entry_id, value in supplied.items():
        quantity, _, cas = entry_id.partition(":")
        if quantity in (*_FIELDS, _LIMIT) and cas and _may_fill(ledger, cas):
            _set(ledger, cas, quantity, value)


def _may_fill(ledger: Ledger, cas: str) -> bool:
    return ledger.cas is None or _digits(ledger.cas) == _digits(cas)


def _set(ledger: Ledger, cas: str, quantity: str, value: float) -> None:
    ledger.cas = ledger.cas or cas
    _, props = ledger.properties or (cas, PropertiesPayload())
    if _has(props, quantity):
        return
    update = {
        "sources": {**props.sources, quantity: USER_PROVIDED},
        "warnings": [w for w in props.warnings if quantity not in w.lower()],
        **_value_update(quantity, value),
    }
    ledger.properties = (cas, props.model_copy(update=update))


def _has(props: PropertiesPayload, quantity: str) -> bool:
    if quantity == _LIMIT:
        return (
            props.occupational_limits is not None
            and props.occupational_limits.oel_twa_mg_m3 is not None
        )
    return getattr(props, quantity) is not None


def _value_update(quantity: str, value: float) -> dict[str, object]:
    if quantity == _LIMIT:
        return {"occupational_limits": LimitsPayload(oel_twa_mg_m3=value, oel_source=USER_PROVIDED)}
    return {quantity: value}


def _digits(cas: str) -> str:
    return "".join(c for c in cas if c.isdigit())
