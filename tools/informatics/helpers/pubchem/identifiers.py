"""Tell a CAS number, a SMILES and a name apart, and canonicalize SMILES with RDKit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from rdkit import Chem, rdBase

from commons.cas import format_cas

IdentifierKind = Literal["cas", "smiles", "name"]


@dataclass(frozen=True)
class Identifier:
    """A chemical identifier, ready to search PubChem with.

    Attributes:
        kind: ``"cas"``, ``"smiles"`` or ``"name"``.
        query: The hyphenated CAS number, the canonical SMILES or the trimmed name.
    """

    kind: IdentifierKind
    query: str


def _parse(smiles: str) -> Chem.Mol | None:
    """Return the molecule, or None if ``smiles`` is unparseable or has no atoms."""
    _quiet = rdBase.BlockLogs()  # RDKit would print every parse error to stderr
    # The stubs type the result as Mol, but RDKit returns None for an unparseable SMILES.
    mol = cast(Chem.Mol | None, Chem.MolFromSmiles(smiles))
    del _quiet
    return mol if mol is not None and mol.GetNumAtoms() > 0 else None


def canonical_smiles(smiles: str) -> str:
    """Return the RDKit canonical SMILES of ``smiles``.

    Raises:
        ValueError: If ``smiles`` is blank or RDKit cannot parse it; the message names it.
    """
    text = smiles.strip()
    mol = _parse(text) if text else None
    if mol is None:
        raise ValueError(f"RDKit could not parse SMILES {smiles!r}")
    return Chem.MolToSmiles(mol)


def _detect(text: str) -> IdentifierKind:
    if format_cas(text) is not None:
        return "cas"
    return "smiles" if _parse(text) is not None else "name"


def prepare_identifier(identifier: str, kind: IdentifierKind | None = None) -> Identifier:
    """Classify ``identifier`` and normalize it for a PubChem search.

    A valid CAS number (check digit included) is a CAS number; otherwise a string RDKit can
    parse is a SMILES; anything else is a name. A name that is also a valid SMILES (``CO``,
    ``Cu``) is therefore read as a SMILES unless ``kind`` says otherwise.

    Args:
        identifier: A CAS number, a SMILES or a chemical name.
        kind: Skip the detection and treat ``identifier`` as this kind.

    Returns:
        The kind and the query to search with (hyphenated CAS, canonical SMILES, trimmed name).

    Raises:
        ValueError: If ``identifier`` is blank, is stated to be a SMILES that RDKit cannot
            parse, or is stated to be a CAS number that is not valid.
    """
    text = identifier.strip()
    if not text:
        raise ValueError("the chemical identifier is empty")
    chosen = kind or _detect(text)
    if chosen == "smiles":
        return Identifier("smiles", canonical_smiles(text))
    if chosen == "cas":
        cas = format_cas(text)
        if cas is None:
            raise ValueError(f"{identifier!r} is not a valid CAS registry number")
        return Identifier("cas", cas)
    return Identifier("name", text)
