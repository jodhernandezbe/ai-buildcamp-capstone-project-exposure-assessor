"""CAS number -> canonical SMILES lookup via PubChem and RDKit."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import cast
from urllib.parse import quote

import httpx
from rdkit import Chem

from config.loader import PubChemSettings, get_settings

logger = logging.getLogger(__name__)

_SMILES_FIELDS = ("CanonicalSMILES", "ConnectivitySMILES", "SMILES")


def normalize_cas(cas_number: str) -> str:
    """Strip whitespace and hyphens so formatting variants share one cache key."""
    return cas_number.strip().replace("-", "").replace(" ", "")


def canonicalize(smiles: str) -> str | None:
    """Return the RDKit canonical form of ``smiles``, or None if RDKit cannot parse it."""
    mol = Chem.MolFromSmiles(smiles)  # pyright: ignore[reportUnknownMemberType]
    # RDKit stubs omit None, but MolFromSmiles returns None for invalid SMILES.
    if mol is None:  # pyright: ignore[reportUnnecessaryComparison]
        return None
    return Chem.MolToSmiles(mol, canonical=True)  # pyright: ignore[reportUnknownMemberType]


class SmilesLookup:
    """Resolve CAS registry numbers to canonical SMILES using PubChem.

    PubChem resolves CAS numbers as compound-name synonyms, so an ambiguous synonym could
    in principle map to the wrong compound; acceptable for screening-level use.
    Results are cached per normalized CAS number. Found SMILES and definitive misses
    (HTTP 404) are cached; network errors and other failures are not, so they can be retried.
    """

    def __init__(
        self,
        settings: PubChemSettings | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a lookup.

        Args:
            settings: PubChem settings; defaults to ``config/settings.toml``.
            client: HTTP client (injectable for tests); a default one is created if omitted.
            sleep: Function used to wait ``settings.delay_seconds`` before each request.
        """
        self._settings = settings or get_settings()
        self._client = client or httpx.Client(timeout=self._settings.timeout_seconds)
        self._sleep = sleep
        self._cache: dict[str, str | None] = {}

    def get_canonical_smiles(self, cas_number: str) -> str | None:
        """Look up the canonical SMILES for a CAS registry number.

        Args:
            cas_number: CAS registry number, e.g. "71-43-2" (hyphens/whitespace optional).

        Returns:
            RDKit-canonical SMILES (PubChem's raw SMILES if RDKit cannot parse it), or None
            if the input is blank, PubChem has no match, or the request fails.
        """
        if not cas_number or not cas_number.strip():
            return None
        key = normalize_cas(cas_number)
        if key in self._cache:
            return self._cache[key]
        smiles, cacheable = self._fetch(cas_number.strip())
        if cacheable:
            self._cache[key] = smiles
        return smiles

    def _fetch(self, identifier: str) -> tuple[str | None, bool]:
        url = self._settings.compound_property_url.format(identifier=quote(identifier, safe=""))
        self._sleep(self._settings.delay_seconds)
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            logger.debug("PubChem request failed for %r: %s", identifier, exc)
            return None, False
        if response.status_code == 404:
            logger.debug("PubChem has no match for %r", identifier)
            return None, True
        if response.status_code != 200:
            logger.debug("PubChem returned %s for %r", response.status_code, identifier)
            return None, False
        raw = self._extract_raw_smiles(response)
        if raw is None:
            return None, False
        return canonicalize(raw) or raw, True

    @staticmethod
    def _extract_raw_smiles(response: httpx.Response) -> str | None:
        try:
            payload = cast(dict[str, dict[str, list[dict[str, object]]]], response.json())
            props = payload["PropertyTable"]["Properties"][0]
        except (ValueError, KeyError, IndexError, TypeError):
            logger.debug("Malformed PubChem response")
            return None
        for field in _SMILES_FIELDS:
            value = props.get(field)
            if isinstance(value, str) and value:
                return value
        return None
