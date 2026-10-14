"""SMILES -> DTXSID -> physical-chemical properties via the EPA CompTox API."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Mapping, Sequence
from typing import cast
from urllib.parse import quote

import httpx

from config.loader import ComptoxSettings, get_comptox_settings
from tools.schemas import PropertyValue

logger = logging.getLogger(__name__)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def select_value(entry: Mapping[str, object]) -> PropertyValue | None:
    """Pick the experimental median of a CompTox property summary, else the predicted median.

    Args:
        entry: One element of the CompTox property summary list.

    Returns:
        The value with its unit as reported (no conversion) and its source, or None if the
        entry has neither an experimental nor a predicted median or has no unit.
    """
    unit = entry.get("unit")
    if not isinstance(unit, str):
        return None
    experimental = _number(entry.get("experimentalMedian"))
    if experimental is not None:
        return {"value": experimental, "unit": unit, "source": "experimental"}
    predicted = _number(entry.get("predictedMedian"))
    if predicted is not None:
        return {"value": predicted, "unit": unit, "source": "predicted"}
    return None


class ComptoxLookup:
    """Fetch configured chemical properties from CompTox starting from a SMILES.

    Which properties are extracted comes from ``config/settings.toml``. Results are cached
    per SMILES. Found results and definitive misses (HTTP 404 or an empty match list) are
    cached; network errors and other failures are not, so they can be retried.
    """

    def __init__(
        self,
        settings: ComptoxSettings | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Create a lookup.

        Args:
            settings: CompTox settings; defaults to ``config/settings.toml``.
            client: HTTP client (injectable for tests); a default one is created if omitted.
            sleep: Function used to wait ``settings.delay_seconds`` before each request.
            environ: Environment mapping the API key is read from; defaults to ``os.environ``.
        """
        self._settings = settings or get_comptox_settings()
        self._client = client or httpx.Client(timeout=self._settings.timeout_seconds)
        self._sleep = sleep
        self._environ = os.environ if environ is None else environ
        self._cache: dict[str, dict[str, PropertyValue]] = {}

    def get_properties(self, smiles: str) -> dict[str, PropertyValue]:
        """Look up the configured properties for a chemical.

        Args:
            smiles: Canonical SMILES, e.g. "c1ccccc1" for benzene.

        Returns:
            Mapping of configured property key (e.g. "vapor_pressure") to its value, unit
            (as reported by CompTox) and source ("experimental" preferred over "predicted").
            Properties with no value are omitted. Empty if the SMILES is blank, CompTox has
            no match, or a request fails.

        Raises:
            RuntimeError: If the API-key environment variable is unset or blank.
        """
        if not smiles or not smiles.strip():
            return {}
        key = smiles.strip()
        if key in self._cache:
            return dict(self._cache[key])
        headers = {self._settings.api_key_header: self._api_key()}
        dtxsid, cacheable = self._fetch_dtxsid(key, headers)
        result: dict[str, PropertyValue] = {}
        if dtxsid is not None:
            summary, cacheable = self._fetch_summary(dtxsid, headers)
            result = self._extract(summary) if summary is not None else {}
        if cacheable:
            self._cache[key] = result
        return dict(result)

    def _api_key(self) -> str:
        name = self._settings.api_key_env_var
        value = self._environ.get(name, "").strip()
        if not value:
            raise RuntimeError(f"CompTox API key not set: define the {name} environment variable")
        return value

    def _get_json(
        self, url: str, headers: Mapping[str, str], what: str
    ) -> tuple[object | None, bool]:
        """Return (parsed JSON or None, definitive); definitive False means a transient failure."""
        self._sleep(self._settings.delay_seconds)
        try:
            response = self._client.get(url, headers=dict(headers))
        except httpx.HTTPError as exc:
            logger.debug("CompTox %s request failed: %s", what, exc)
            return None, False
        if response.status_code == 404:
            logger.debug("CompTox has no match for %s", what)
            return None, True
        if response.status_code != 200:
            logger.debug("CompTox returned %s for %s", response.status_code, what)
            return None, False
        try:
            return cast(object, response.json()), True
        except ValueError:
            logger.debug("Malformed CompTox %s response", what)
            return None, False

    def _fetch_dtxsid(self, smiles: str, headers: Mapping[str, str]) -> tuple[str | None, bool]:
        url = self._settings.dtxsid_by_smiles_url.format(smiles=quote(smiles, safe=""))
        payload, definitive = self._get_json(url, headers, "DTXSID search")
        if payload is None:
            return None, definitive
        if not isinstance(payload, list):
            logger.debug("Malformed CompTox DTXSID response")
            return None, False
        matches = cast(list[object], payload)
        if not matches:
            return None, True
        if len(matches) > 1:
            logger.debug("CompTox returned %d matches; using the first", len(matches))
        first = matches[0]
        dtxsid = (
            cast(dict[object, object], first).get("dtxsid") if isinstance(first, dict) else None
        )
        if not isinstance(dtxsid, str) or not dtxsid:
            logger.debug("CompTox match has no dtxsid")
            return None, False
        return dtxsid, True

    def _fetch_summary(
        self, dtxsid: str, headers: Mapping[str, str]
    ) -> tuple[Sequence[Mapping[str, object]] | None, bool]:
        url = self._settings.properties_by_dtxsid_url.format(dtxsid=quote(dtxsid, safe=""))
        payload, definitive = self._get_json(url, headers, "property search")
        if payload is None:
            return None, definitive
        if not isinstance(payload, list):
            logger.debug("Malformed CompTox property response")
            return None, False
        entries = [
            {str(k): v for k, v in cast(dict[object, object], item).items()}
            for item in cast(list[object], payload)
            if isinstance(item, dict)
        ]
        return entries, True

    def _extract(self, summary: Sequence[Mapping[str, object]]) -> dict[str, PropertyValue]:
        by_name: dict[str, Mapping[str, object]] = {}
        for entry in summary:
            name = entry.get("propName")
            if isinstance(name, str):
                by_name.setdefault(name, entry)
        result: dict[str, PropertyValue] = {}
        for spec in self._settings.properties:
            entry = by_name.get(spec.name)
            value = select_value(entry) if entry is not None else None
            if value is not None:
                result[spec.key] = value
        return result
