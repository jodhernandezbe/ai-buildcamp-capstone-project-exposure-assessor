"""Map framing hints: the extent of the placed facilities and when the camera should move."""

from __future__ import annotations

from collections.abc import Sequence

from api.schemas.workspace import BoundingBox, Facility

FramingKey = frozenset[tuple[str, float, float, float | None]]


def _positions(facility: Facility) -> list[tuple[float, float]]:
    """``(longitude, latitude)`` of a facility and of every vertex of its drawn buffer."""
    ring = facility.buffer.coordinates[0] if facility.buffer else []
    return [(facility.longitude, facility.latitude), *((p[0], p[1]) for p in ring)]


def bounds(facilities: Sequence[Facility]) -> BoundingBox | None:
    """The smallest box holding every placed facility and its buffer; None when none is placed."""
    points = [p for facility in facilities for p in _positions(facility)]
    if not points:
        return None
    lons, lats = [p[0] for p in points], [p[1] for p in points]
    return BoundingBox(west=min(lons), south=min(lats), east=max(lons), north=max(lats))


def framing_key(facilities: Sequence[Facility]) -> FramingKey:
    """What the camera frames: each placed facility and the radius (km) of its buffer, if any."""
    return frozenset(
        (f.frs_id, f.latitude, f.longitude, f.receptors.radius_km if f.receptors else None)
        for f in facilities
    )


def next_version(previous: tuple[int, FramingKey] | None, facilities: Sequence[Facility]) -> int:
    """The previous version, plus one when the placed facilities or buffers changed."""
    key = framing_key(facilities)
    if previous is None:
        return 1 if key else 0
    version, before = previous
    return version + 1 if key != before else version
