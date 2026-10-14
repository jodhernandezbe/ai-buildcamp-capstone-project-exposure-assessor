"""Tests for tools.informatics.helpers.smiles (no network)."""

from __future__ import annotations

import httpx

from config.loader import PubChemSettings
from tools.informatics.helpers.smiles import SmilesLookup

SETTINGS = PubChemSettings(
    base_url="https://pubchem.test/pug",
    compound_property_path="/name/{identifier}/props",
    delay_seconds=0.5,
    timeout_seconds=1.0,
)


def _lookup(
    handler: httpx.MockTransport | None = None,
    *,
    status: int = 200,
    body: object = None,
    sleeps: list[float] | None = None,
) -> tuple[SmilesLookup, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if isinstance(body, Exception):
            raise body
        return httpx.Response(status, json=body) if body is not None else httpx.Response(status)

    client = httpx.Client(transport=handler or httpx.MockTransport(respond))
    record = sleeps if sleeps is not None else []
    return SmilesLookup(SETTINGS, client, sleep=record.append), requests


def _props(**fields: str) -> dict[str, dict[str, list[dict[str, object]]]]:
    return {"PropertyTable": {"Properties": [{"CID": 1, **fields}]}}


def test_known_cas_is_canonicalized() -> None:
    lookup, requests = _lookup(body=_props(CanonicalSMILES="C1=CC=CC=C1"))
    assert lookup.get_canonical_smiles("71-43-2") == "c1ccccc1"
    assert str(requests[0].url) == "https://pubchem.test/pug/name/71-43-2/props"


def test_unknown_cas_returns_none() -> None:
    lookup, _ = _lookup(status=404, body={"Fault": {}})
    assert lookup.get_canonical_smiles("0-00-0") is None


def test_blank_input_skips_request() -> None:
    lookup, requests = _lookup(body=_props(CanonicalSMILES="C"))
    assert lookup.get_canonical_smiles("  ") is None
    assert lookup.get_canonical_smiles("") is None
    assert requests == []


def test_field_fallback() -> None:
    lookup, _ = _lookup(body=_props(ConnectivitySMILES="CCO"))
    assert lookup.get_canonical_smiles("64-17-5") == "CCO"


def test_unparseable_smiles_returned_raw() -> None:
    lookup, _ = _lookup(body=_props(CanonicalSMILES="not-a-smiles(("))
    assert lookup.get_canonical_smiles("1-1-1") == "not-a-smiles(("


def test_network_error_not_cached() -> None:
    lookup, requests = _lookup(body=httpx.ConnectError("boom"))
    assert lookup.get_canonical_smiles("71-43-2") is None
    assert lookup.get_canonical_smiles("71-43-2") is None
    assert len(requests) == 2


def test_malformed_response_returns_none() -> None:
    lookup, _ = _lookup(body={"unexpected": 1})
    assert lookup.get_canonical_smiles("71-43-2") is None


def test_cache_across_formatting_variants() -> None:
    lookup, requests = _lookup(body=_props(CanonicalSMILES="CCO"))
    lookup.get_canonical_smiles("64-17-5")
    lookup.get_canonical_smiles(" 64175 ")
    assert len(requests) == 1


def test_404_miss_is_cached() -> None:
    lookup, requests = _lookup(status=404, body={"Fault": {}})
    lookup.get_canonical_smiles("0-00-0")
    lookup.get_canonical_smiles("0-00-0")
    assert len(requests) == 1


def test_delay_honored_only_on_cache_miss() -> None:
    sleeps: list[float] = []
    lookup, _ = _lookup(body=_props(CanonicalSMILES="CCO"), sleeps=sleeps)
    lookup.get_canonical_smiles("64-17-5")
    lookup.get_canonical_smiles("64-17-5")
    assert sleeps == [0.5]
