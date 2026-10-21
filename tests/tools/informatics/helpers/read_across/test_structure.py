"""Tests for SMILES parsing, ECFP4 bits and molecular weight."""

from __future__ import annotations

import numpy as np
import pytest

from config.read_across import FingerprintSettings
from tools.informatics.helpers.read_across.structure import describe

ECFP4 = FingerprintSettings(radius=2, n_bits=1024)


def test_canonical_bits_and_weight() -> None:
    found = describe("C(C)CCCC", ECFP4)
    assert found is not None
    assert found.smiles == "CCCCCC"
    assert found.bits.shape == (1024,)
    assert found.bits.dtype == np.uint8
    assert set(np.unique(found.bits).tolist()) <= {0, 1}
    assert found.molecular_weight == pytest.approx(86.18, abs=0.01)


def test_same_molecule_same_bits() -> None:
    a, b = describe("CCCCCC", ECFP4), describe("C(CCCCC)", ECFP4)
    assert a is not None and b is not None
    assert np.array_equal(a.bits, b.bits)


def test_configured_width() -> None:
    found = describe("CCO", FingerprintSettings(radius=2, n_bits=64))
    assert found is not None and found.bits.shape == (64,)


@pytest.mark.parametrize("smiles", ["", "   ", "C1CC", "CC(C", "not a smiles"])
def test_unparseable_is_none(smiles: str) -> None:
    assert describe(smiles, ECFP4) is None


def test_salt_kept_as_given() -> None:
    found = describe("[Na+].[Cl-]", ECFP4)
    assert found is not None and "." in found.smiles


def test_weight_does_not_depend_on_the_smiles_spelling() -> None:
    """The same molecule from two spellings must store the same bytes (no ulp noise)."""
    a = describe("OC(=O)c1ccccc1C(F)(F)F", ECFP4)
    b = describe("FC(F)(F)c1ccccc1C(O)=O", ECFP4)
    assert a is not None and b is not None
    assert a.molecular_weight == b.molecular_weight
    assert a.molecular_weight == round(a.molecular_weight, 4)
