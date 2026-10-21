"""Projectors of the chemistry tools: properties and the read-across surrogate."""

from __future__ import annotations

from api.services.projectors.ledger import Ledger, ToolExchange, text
from api.services.projectors.payloads import PropertiesPayload, ReadAcrossPayload


def project_properties(exchange: ToolExchange, ledger: Ledger) -> None:
    """The properties and toxicity values of the CAS number the model asked about."""
    cas = text(exchange.args, "cas_number")
    result = ledger.read(exchange, PropertiesPayload)
    if result is not None and cas is not None:
        ledger.note_cas(exchange)
        ledger.properties = (cas, result)


def project_read_across(exchange: ToolExchange, ledger: Ledger) -> None:
    """The read-across outcome of the CAS number the model asked about."""
    result = ledger.read(exchange, ReadAcrossPayload)
    if result is not None:
        ledger.note_cas(exchange)
        ledger.read_across = (result.query_cas, result)
