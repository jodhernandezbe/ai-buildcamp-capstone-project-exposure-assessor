"""The configured values the workspace needs to attribute results and to grade risk."""

from __future__ import annotations

from dataclasses import dataclass

from api.schemas.workspace import Status
from config.exposure_graph import GraphText
from config.ui import RiskThresholds


@dataclass(frozen=True)
class WorkspaceRules:
    """Thresholds, the tolerance for matching points to facilities and the default radius.

    Attributes:
        thresholds: HQ and cancer-risk thresholds of concern (unitless).
        coordinate_tolerance_deg: Tolerance for matching a queried point to a facility, degrees.
        default_radius_km: Receptor radius of a population call that gave none, km.
        sector_half_angle_deg: Half-angle of the schematic downwind sector, degrees.
        vertex_spacing_deg: Angular spacing of the vertices of the drawn shapes, degrees.
        graph: Fixed text and units of the exposure graph.
    """

    thresholds: RiskThresholds
    coordinate_tolerance_deg: float
    default_radius_km: float
    sector_half_angle_deg: float
    vertex_spacing_deg: float
    graph: GraphText


SEVERITY: tuple[Status, ...] = ("below", "near", "above")


def hq_status(value: float, thresholds: RiskThresholds) -> Status:
    """Above the HQ of concern, near it (from the lower bound up to it) or below."""
    if value > thresholds.hq_concern:
        return "above"
    return "near" if value >= thresholds.hq_near_lower else "below"


def cancer_status(value: float, thresholds: RiskThresholds) -> Status:
    """Above the upper cancer-risk threshold, below the lower one, near in between."""
    if value > thresholds.cancer_upper:
        return "above"
    return "below" if value < thresholds.cancer_lower else "near"


def worse(first: Status | None, second: Status | None) -> Status | None:
    """The more severe of two statuses; None when neither is known."""
    known: list[Status] = [s for s in (first, second) if s is not None]
    return max(known, key=SEVERITY.index) if known else None
