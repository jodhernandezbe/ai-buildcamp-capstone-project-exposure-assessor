"""Tests for the PubChem SMILES and molecular weight lookup (no network)."""

from __future__ import annotations

import httpx
import pytest

from config.read_across import load_read_across_settings
from tests.tools.informatics.read_across_fakes import Server, answer, pubchem_body
from tools.informatics.helpers.read_across.pubchem import PubchemCompound, fetch_compound

SETTINGS = load_read_across_settings().pubchem


def _fetch(server: Server, cas: str = "107-83-5") -> PubchemCompound | str:
    return fetch_compound(cas, server.client, SETTINGS)


def test_reads_smiles_and_string_weight() -> None:
    server = Server(answer(pubchem_body(SMILES="CCCC(C)C", MolecularWeight="86.18")))
    assert _fetch(server) == PubchemCompound("CCCC(C)C", 86.18)
    assert server.urls == [SETTINGS.url("107-83-5")]


def test_first_configured_property_wins() -> None:
    body = pubchem_body(CanonicalSMILES="CCO", SMILES="OCC", MolecularWeight=46.07)
    found = _fetch(Server(answer(body)))
    assert isinstance(found, PubchemCompound) and found.smiles == "CCO"


def test_connectivity_alias_used() -> None:
    found = _fetch(Server(answer(pubchem_body(ConnectivitySMILES="CCO"))))
    assert isinstance(found, PubchemCompound) and found.smiles == "CCO"


@pytest.mark.parametrize("weight", [None, "", "n/a", True, -1, 0, "NaN", "inf", [86.0]])
def test_unusable_weight_is_none(weight: object) -> None:
    found = _fetch(Server(answer(pubchem_body(SMILES="CCO", MolecularWeight=weight))))
    assert isinstance(found, PubchemCompound) and found.molecular_weight is None


def test_not_found() -> None:
    found = _fetch(Server(answer({"Fault": {"Code": "PUGREST.NotFound"}}, 404)))
    assert found == "PubChem has no compound for CAS number 107-83-5"


def test_unreachable() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    found = _fetch(Server(fail))
    assert isinstance(found, str) and "could not be reached" in found


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"PropertyTable": {}},
        {"PropertyTable": {"Properties": "x"}},
        pubchem_body(MolecularWeight="86.18"),
        pubchem_body(SMILES="  "),
    ],
)
def test_malformed_answer(body: object) -> None:
    assert _fetch(Server(answer(body))) == "PubChem returned no SMILES"


def test_several_compounds_is_ambiguous() -> None:
    body = {"PropertyTable": {"Properties": [{"SMILES": "CCO"}, {"SMILES": "COC"}]}}
    found = _fetch(Server(answer(body)))
    assert isinstance(found, str) and "ambiguous" in found


def test_repeated_same_compound_is_not_ambiguous() -> None:
    body = {"PropertyTable": {"Properties": [{"SMILES": "CCO"}, {"SMILES": "CCO"}]}}
    assert isinstance(_fetch(Server(answer(body))), PubchemCompound)
