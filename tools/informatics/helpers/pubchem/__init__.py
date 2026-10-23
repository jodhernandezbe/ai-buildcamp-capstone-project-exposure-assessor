"""PubChem client: identifiers to CIDs and records, and the fallback for chemical properties."""

from __future__ import annotations

from tools.informatics.helpers.pubchem.client import (
    fetch_pubchem_pug_view_json,
    get_cid_by_identifier,
)
from tools.informatics.helpers.pubchem.lookup import (
    PubchemCandidates,
    PubchemFallback,
    PubchemLookup,
)
from tools.informatics.helpers.pubchem.resolve import Compound, resolve_compound_data
from tools.informatics.helpers.pubchem.transport import build_client

__all__ = [
    "Compound",
    "PubchemCandidates",
    "PubchemFallback",
    "PubchemLookup",
    "build_client",
    "fetch_pubchem_pug_view_json",
    "get_cid_by_identifier",
    "resolve_compound_data",
]
