"""Recover a facility's coordinates from its FRS record when TRI has none."""

from __future__ import annotations

import logging
import math

from config.frs_point import FrsPointSettings
from tools.digits import digit_string
from tools.emissions.helpers.efservice import EfserviceClient, EfserviceError, Row
from tools.emissions.helpers.inventory.reduce import Location

logger = logging.getLogger(__name__)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return None
    return float(value)


def _point(row: Row, settings: FrsPointSettings) -> Location | None:
    latitude = _number(row.get(settings.latitude_field))
    longitude = _number(row.get(settings.longitude_field))
    if latitude is None or longitude is None:
        return None
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return Location(latitude, longitude)


class FrsLocator:
    """Looks up the coordinates of FRS facilities, one request each, remembering answers.

    A failure or an unusable answer gives None (and is remembered), never an exception, so
    the facility is simply reported as without coordinates.
    """

    def __init__(self, client: EfserviceClient, settings: FrsPointSettings) -> None:
        """Args: Envirofacts client (injected); the ``[frs_point]`` settings."""
        self._client = client
        self._settings = settings
        self._known: dict[str, Location | None] = {}

    def __call__(self, frs_id: str) -> Location | None:
        """Return the newest valid point of ``frs_id``, or None."""
        digits = digit_string(frs_id)
        if digits is None:
            return None
        if digits not in self._known:
            self._known[digits] = self._fetch(digits)
        return self._known[digits]

    def _fetch(self, digits: str) -> Location | None:
        try:
            rows = self._client.get_rows(self._settings.path.format(frs_id=digits))
        except EfserviceError as exc:
            logger.warning("FRS coordinates for %s could not be read: %s", digits, exc)
            return None
        newest = sorted(rows, key=lambda row: str(row.get(self._settings.timestamp_field) or ""))
        points = (_point(row, self._settings) for row in reversed(newest))
        return next((point for point in points if point is not None), None)
