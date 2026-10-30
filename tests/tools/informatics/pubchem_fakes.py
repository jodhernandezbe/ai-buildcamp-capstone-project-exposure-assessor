"""Test doubles for the PubChem fallback of fetch_chemical_properties (no network)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from tools.informatics.helpers.comptox import ComptoxLookup
from tools.informatics.helpers.pubchem import PubchemCandidates
from tools.informatics.helpers.pubchem.extract import FieldValue
from tools.informatics.helpers.pubchem.limits import empty_limits
from tools.schemas import OccupationalLimits, PropertyValue, ToxicityValue

DEFAULT_FIELDS = ("molecular_weight", "vapor_pressure", "density")


@dataclass
class FakePubchem:
    """A PubChem fallback that offers fixed candidates and records what it was asked."""

    offered: PubchemCandidates = field(default_factory=PubchemCandidates)
    fields: tuple[str, ...] = DEFAULT_FIELDS
    calls: list[tuple[str, tuple[str, ...]]] = field(default_factory=lambda: [])
    offered_limits: OccupationalLimits | None = None
    limit_calls: list[tuple[str, float | None]] = field(default_factory=lambda: [])

    def candidates(self, cas: str, keys: Sequence[str]) -> PubchemCandidates:
        self.calls.append((cas, tuple(keys)))
        return self.offered

    def limits(self, cas: str, molecular_weight: float | None) -> OccupationalLimits:
        self.limit_calls.append((cas, molecular_weight))
        return self.offered_limits or empty_limits("no limits offered")


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
        notes: Sequence[str] = (),
    ) -> None:
        super().__init__()
        self._stub_weight = weight
        self._stub_properties: dict[str, PropertyValue] = dict(properties) if properties else {}
        self._stub_toxicity: dict[str, ToxicityValue] = dict(toxicity) if toxicity else {}
        self._stub_name = name
        self._stub_notes = list(notes)

    def get_molecular_weight(self, cas_number: str) -> float | None:
        return self._stub_weight

    def get_preferred_name(self, cas_number: str) -> str | None:
        return self._stub_name

    def get_properties(self, cas_number: str) -> dict[str, PropertyValue]:
        return dict(self._stub_properties)

    def get_toxicity_values(self, cas_number: str) -> dict[str, ToxicityValue]:
        return dict(self._stub_toxicity)

    def get_toxicity_notes(self, cas_number: str) -> list[str]:
        return list(self._stub_notes)
