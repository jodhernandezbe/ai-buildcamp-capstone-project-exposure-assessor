"""Test doubles for the PubChem fallback of fetch_chemical_properties (no network)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from tools.informatics.helpers.comptox import ComptoxLookup
from tools.informatics.helpers.pubchem import PubchemCandidates
from tools.informatics.helpers.pubchem.extract import FieldValue
from tools.schemas import PropertyValue, ToxicityValue

DEFAULT_FIELDS = ("molecular_weight", "vapor_pressure", "density")


@dataclass
class FakePubchem:
    """A PubChem fallback that offers fixed candidates and records what it was asked."""

    offered: PubchemCandidates = field(default_factory=PubchemCandidates)
    fields: tuple[str, ...] = DEFAULT_FIELDS
    calls: list[tuple[str, tuple[str, ...]]] = field(default_factory=lambda: [])

    def candidates(self, cas: str, keys: Sequence[str]) -> PubchemCandidates:
        self.calls.append((cas, tuple(keys)))
        return self.offered


def offer(**values: tuple[float, str]) -> PubchemCandidates:
    """Candidates for fields given as ``key=(value, unit)``."""
    return PubchemCandidates({k: FieldValue(v, u, 1) for k, (v, u) in values.items()})


class StubComptox(ComptoxLookup):
    """A CompTox lookup answering from fixed values (nothing is requested)."""

    def __init__(
        self,
        weight: float | None = None,
        properties: Mapping[str, PropertyValue] | None = None,
        toxicity: Mapping[str, ToxicityValue] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__()
        self._stub_weight = weight
        self._stub_properties: dict[str, PropertyValue] = dict(properties) if properties else {}
        self._stub_toxicity: dict[str, ToxicityValue] = dict(toxicity) if toxicity else {}
        self._stub_name = name

    def get_molecular_weight(self, cas_number: str) -> float | None:
        return self._stub_weight

    def get_preferred_name(self, cas_number: str) -> str | None:
        return self._stub_name

    def get_properties(self, cas_number: str) -> dict[str, PropertyValue]:
        return dict(self._stub_properties)

    def get_toxicity_values(self, cas_number: str) -> dict[str, ToxicityValue]:
        return dict(self._stub_toxicity)
