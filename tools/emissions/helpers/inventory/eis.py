"""Give the listed facilities their EIS (NEI) facility IDs, many per request.

The NEI's facility key is the EIS ID, registered in FRS under the facility's FRS ID. FRS also
holds the same site under more than one FRS ID at times, and TRI's ID is not always the one
with the EIS registration. A facility whose own ID has none is matched to another FRS record
of exactly the same site name in the same state within a short distance, and only when exactly
one such record has EIS registrations; anything less certain leaves the facility without an
EIS ID and says why.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import quote

from config.frs_eis import FrsEisSettings
from tools.digits import digit_string
from tools.emissions.helpers.efservice import EfserviceClient, EfserviceError, Row
from tools.schemas import EmissionRecord

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0
EisIds = tuple[str, ...]
UNREACHABLE_NOTE = "the EIS registrations could not be looked up (FRS is unreachable)"


@dataclass(frozen=True)
class Site:
    """An FRS site row: its registry ID, name, state and coordinates (decimal degrees)."""

    frs_id: str
    name: str
    state: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Twin:
    """What the same-site search found for one facility."""

    eis_ids: EisIds
    note: str


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance (km) between two points given in decimal degrees (haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return None
    return float(value)


def _digits(value: object) -> str | None:
    return digit_string(value) if isinstance(value, str | int) else None


def _site(row: Row, settings: FrsEisSettings) -> Site | None:
    """The row as a site, or None when any part of it is missing or implausible."""
    frs_id = _digits(row.get(settings.registry_field))
    name = str(row.get(settings.name_field) or "").strip()
    state = str(row.get(settings.state_field) or "").strip().upper()
    latitude = _number(row.get(settings.latitude_field))
    longitude = _number(row.get(settings.longitude_field))
    if frs_id is None or not name or not state or latitude is None or longitude is None:
        return None
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return Site(frs_id, name, state, latitude, longitude)


class EisResolver:
    """Finds the EIS IDs of facilities in bulk, and of their FRS twins when they have none.

    One request answers up to ``batch_size`` facilities; the same-site searches (one request
    each) run ``twin_workers`` at a time. A failed request leaves those facilities without EIS
    IDs and a note, never an exception.
    """

    def __init__(self, client: EfserviceClient, settings: FrsEisSettings) -> None:
        """Args: client for the FRS service (injected); the ``[frs_eis]`` settings."""
        self._client = client
        self._settings = settings

    def __call__(self, records: Sequence[EmissionRecord]) -> list[EmissionRecord]:
        """Copies of ``records`` with ``eis_ids`` filled and ``eis_note`` saying how, if at all."""
        own = self._registrations([r["frs_id"] for r in records])
        if own is None:
            return [{**r, "eis_ids": [], "eis_note": UNREACHABLE_NOTE} for r in records]
        missing = [r["frs_id"] for r in records if not own.get(r["frs_id"])]
        twins = self._twins_of(missing) if missing else {}
        out: list[EmissionRecord] = []
        for record in records:
            ids = own.get(record["frs_id"], ())
            if ids:
                out.append({**record, "eis_ids": list(ids), "eis_note": None})
                continue
            twin = twins[record["frs_id"]]
            out.append({**record, "eis_ids": list(twin.eis_ids), "eis_note": twin.note})
        return out

    def _rows(self, path: str) -> list[Row] | None:
        try:
            return self._client.get_rows(path)
        except EfserviceError as exc:
            logger.warning("FRS query failed: %s", exc)
            return None

    def _registrations(self, frs_ids: Sequence[str]) -> dict[str, EisIds] | None:
        """FRS ID -> its distinct EIS IDs (empty when none); None when a request failed."""
        wanted = [d for d in dict.fromkeys(digit_string(i) for i in frs_ids) if d]
        found: dict[str, list[str]] = {d: [] for d in wanted}
        size = self._settings.batch_size
        for start in range(0, len(wanted), size):
            batch = wanted[start : start + size]
            rows = self._rows(self._settings.eis_path.format(frs_ids=",".join(batch)))
            if rows is None:
                return None
            for row in rows:
                registry = _digits(row.get(self._settings.registry_field))
                eis = _digits(row.get(self._settings.eis_id_field))
                if registry in found and eis is not None and eis not in found[registry]:
                    found[registry].append(eis)
        return {frs_id: tuple(ids) for frs_id, ids in found.items()}

    def _sites(self, frs_ids: Sequence[str]) -> dict[str, Site]:
        """The FRS site rows of these IDs (missing when absent, unusable or unreachable)."""
        sites: dict[str, Site] = {}
        size = self._settings.batch_size
        for start in range(0, len(frs_ids), size):
            batch = frs_ids[start : start + size]
            rows = self._rows(self._settings.sites_path.format(frs_ids=",".join(batch))) or []
            for row in rows:
                site = _site(row, self._settings)
                if site is not None and site.frs_id in batch:
                    sites.setdefault(site.frs_id, site)
        return sites

    def _twins(self, site: Site) -> list[tuple[Site, float]]:
        """Other FRS records of the same name and state within reach, nearest first."""
        path = self._settings.twins_path.format(
            name=quote(site.name, safe=""), state=quote(site.state, safe="")
        )
        rows = self._rows(path) or []
        nearby: list[tuple[Site, float]] = []
        for row in rows:
            other = _site(row, self._settings)
            if other is None or other.frs_id == site.frs_id:
                continue
            if other.name != site.name or other.state != site.state:
                continue
            apart = distance_km(site.latitude, site.longitude, other.latitude, other.longitude)
            if apart <= self._settings.max_twin_distance_km:
                nearby.append((other, apart))
        return sorted(nearby, key=lambda item: item[1])

    def _twins_of(self, frs_ids: Sequence[str]) -> dict[str, Twin]:
        """What the same-site search found for each facility without its own registration.

        The searches run ``twin_workers`` at a time; the registrations of every twin found are
        then read together.
        """
        sites = self._sites(frs_ids)
        workers = max(1, min(self._settings.twin_workers, len(sites)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            nearby = dict(zip(sites, pool.map(self._twins, sites.values()), strict=True))
        others = [other.frs_id for near in nearby.values() for other, _ in near]
        registered = (self._registrations(others) or {}) if others else {}
        return {
            frs_id: _pick(frs_id, frs_id in sites, nearby.get(frs_id, []), registered)
            for frs_id in frs_ids
        }


def _pick(
    frs_id: str, located: bool, nearby: list[tuple[Site, float]], registered: dict[str, EisIds]
) -> Twin:
    """EIS IDs borrowed from the one FRS twin that has them, else none with the reason."""
    none = f"FRS ID {frs_id} has no EIS registration"
    if not located:
        return Twin((), none)
    if not nearby:
        return Twin((), f"{none}, and no other FRS record of the same site was found")
    with_eis = [(other, apart) for other, apart in nearby if registered.get(other.frs_id)]
    if len(with_eis) != 1:
        why = "none has one" if not with_eis else f"{len(with_eis)} have their own"
        return Twin((), f"{none}; of the FRS records of the same site nearby, {why}")
    other, apart = with_eis[0]
    note = (
        f"EIS IDs are those of FRS ID {other.frs_id}, the same site name "
        f"{round(apart * 1000)} m away, since {none}"
    )
    return Twin(registered[other.frs_id], note)
