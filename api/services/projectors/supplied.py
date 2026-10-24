"""The values the user supplied for missing benchmarks, shown on the chemical as theirs."""

from __future__ import annotations

from collections.abc import Mapping

from api.services.projectors.ledger import Ledger
from api.services.projectors.payloads import PropertiesPayload

USER_PROVIDED = "user-provided"
_BENCHMARKS = ("rfc", "iur")  # the PropertiesPayload fields a missing value can fill


def apply_supplied(ledger: Ledger, supplied: Mapping[str, float]) -> None:
    """Fill the chemical's empty benchmarks with the values the user supplied, labelled as theirs.

    Keys are entry IDs such as ``rfc:71-43-2``. A value is only set where the chemical has none,
    and only for the CAS number the thread is about (or the first one, when none is known yet).
    The value is in the target unit the entry asked for, so it is shown as given.
    """
    for entry_id, value in supplied.items():
        quantity, _, cas = entry_id.partition(":")
        if quantity in _BENCHMARKS and cas and _may_fill(ledger, cas):
            _set(ledger, cas, quantity, value)


def _may_fill(ledger: Ledger, cas: str) -> bool:
    return ledger.cas is None or _digits(ledger.cas) == _digits(cas)


def _set(ledger: Ledger, cas: str, quantity: str, value: float) -> None:
    ledger.cas = ledger.cas or cas
    _, props = ledger.properties or (cas, PropertiesPayload())
    if getattr(props, quantity) is not None:
        return
    updated = props.model_copy(
        update={
            quantity: value,
            "sources": {**props.sources, quantity: USER_PROVIDED},
            "warnings": [w for w in props.warnings if quantity not in w.lower()],
        }
    )
    ledger.properties = (cas, updated)


def _digits(cas: str) -> str:
    return "".join(c for c in cas if c.isdigit())
