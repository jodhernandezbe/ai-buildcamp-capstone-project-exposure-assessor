"""Tests for CAS / SMILES / name detection and RDKit canonicalization (no network)."""

from __future__ import annotations

import pytest

from tools.informatics.helpers.pubchem.identifiers import (
    Identifier,
    canonical_smiles,
    prepare_identifier,
)


def test_cas_number_is_detected() -> None:
    assert prepare_identifier("106-97-8") == Identifier("cas", "106-97-8")


def test_bare_digit_cas_number_is_hyphenated() -> None:
    assert prepare_identifier(" 110543 ") == Identifier("cas", "110-54-3")


def test_smiles_is_detected_and_canonicalized() -> None:
    assert prepare_identifier("CCCC") == Identifier("smiles", "CCCC")


def test_equivalent_smiles_give_the_same_query() -> None:
    assert prepare_identifier("OCC").query == prepare_identifier("C(O)C").query == "CCO"


def test_name_is_detected() -> None:
    assert prepare_identifier("  n-hexane ") == Identifier("name", "n-hexane")


def test_wrong_check_digit_is_not_a_cas_number() -> None:
    assert prepare_identifier("106-97-9").kind != "cas"


def test_explicit_kind_skips_detection() -> None:
    assert prepare_identifier("CO", kind="name") == Identifier("name", "CO")
    assert prepare_identifier("CO").kind == "smiles"


def test_malformed_smiles_raises_naming_it() -> None:
    with pytest.raises(ValueError, match=r"RDKit could not parse SMILES 'C\(C'"):
        prepare_identifier("C(C", kind="smiles")


def test_stated_cas_that_is_invalid_raises() -> None:
    with pytest.raises(ValueError, match="not a valid CAS"):
        prepare_identifier("106-97-9", kind="cas")


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_identifier_raises(text: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        prepare_identifier(text)


def test_canonical_smiles_rejects_blank() -> None:
    with pytest.raises(ValueError, match="could not parse"):
        canonical_smiles("  ")


def test_canonical_smiles_keeps_special_characters() -> None:
    assert canonical_smiles("C/C=C/C") == "C/C=C/C"
