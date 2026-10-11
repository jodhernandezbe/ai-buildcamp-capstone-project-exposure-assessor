"""Meteorology lookup tool."""

from __future__ import annotations

from langchain_core.tools import tool

from tools.schemas import Meteorology


@tool
def get_meteorological_boundary(latitude: float, longitude: float) -> Meteorology:
    """Get representative meteorological conditions for dispersion modeling at a point.

    Purpose:
        Supplies the wind and atmospheric stability inputs of the transport model
        used by `calculate_exposure_metrics`.

    Args:
        latitude: Decimal degrees (WGS84), positive north.
        longitude: Decimal degrees (WGS84), positive east.

    Returns:
        A dict with:
        - wind_speed: m/s
        - wind_direction: degrees clockwise from north, direction the wind blows from
        - stability_class: Pasquill-Gifford class, "A" (very unstable) to "F" (very stable)
    """
    raise NotImplementedError
