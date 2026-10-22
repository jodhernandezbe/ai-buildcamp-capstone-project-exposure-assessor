"""Attribution: a result belongs to a facility only when it matches exactly one, by identifiers."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from api.schemas.workspace import Unattributed
from api.services.projectors.payloads import EmissionPayload


class Point(Protocol):
    """Anything placed at a latitude and longitude (decimal degrees)."""

    @property
    def latitude(self) -> float: ...

    @property
    def longitude(self) -> float: ...


NO_MATCH = "it matches none of the facilities found"
AMBIGUOUS = "it matches more than one facility"


@dataclass
class Finder:
    """Ties results to the facilities they match; those matching none or several are listed."""

    records: Mapping[str, EmissionPayload]
    lost: list[Unattributed]

    def of[T](
        self,
        items: Sequence[T],
        matches: Callable[[T, EmissionPayload], bool],
        tool: str,
    ) -> dict[str, T]:
        """Facility FRS ID -> its latest matching item, for items matching exactly one."""
        attached: dict[str, T] = {}
        for item in items:
            hits = [frs_id for frs_id, record in self.records.items() if matches(item, record)]
            if len(hits) == 1:
                attached[hits[0]] = item
            else:
                reason = AMBIGUOUS if hits else NO_MATCH
                self.lost.append(Unattributed(tool=tool, reason=reason))
        return attached


def at_facility(tolerance_deg: float) -> Callable[[Point, EmissionPayload], bool]:
    """Matches a point to a facility whose coordinates equal it within the tolerance."""

    def matches(point: Point, record: EmissionPayload) -> bool:
        return (
            abs(point.latitude - record.latitude) <= tolerance_deg
            and abs(point.longitude - record.longitude) <= tolerance_deg
        )

    return matches


def same_rate(item: tuple[float | str, object], record: EmissionPayload) -> bool:
    """Matches by FRS ID when the item carries one, else by an equal emission rate (g/s)."""
    key = item[0]
    if isinstance(key, str):
        return key == record.frs_id
    return math.isclose(key, record.emission_rate, rel_tol=1e-9, abs_tol=0.0)


def same_doc(item: tuple[str, object], record: EmissionPayload) -> bool:
    """Matches a TRI document control number to the facility's."""
    return item[0] == record.doc_ctrl_num


def same_frs(item: tuple[str, object], record: EmissionPayload) -> bool:
    """Matches an FRS ID to the facility's."""
    return item[0] == record.frs_id
