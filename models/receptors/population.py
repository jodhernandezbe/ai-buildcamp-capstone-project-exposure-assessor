"""Population arithmetic: scaling tract counts to a circle and converting counts to age bands."""

from __future__ import annotations

import math

AGE_BANDS: tuple[str, str, str, str] = ("0-4", "5-17", "18-64", "65+")
_PERCENT = 100.0
_DECIMALS = 2


def _require(value: float, name: str, *, positive: bool = False) -> None:
    ok = not isinstance(value, bool) and math.isfinite(value) and value >= 0
    if not ok or (positive and value == 0):
        word = "positive" if positive else "non-negative"
        raise ValueError(f"{name} must be a finite, {word} number, got {value!r}")


def scale_to_circle(count: float, circle_area_m2: float, land_area_m2: float) -> float:
    """Scale a residents count from whole tracts to the part of them inside a circle.

    Assumes residents are spread evenly over the tracts' land area, so the circle holds the
    fraction ``circle area / land area`` of them, never more than all of them.

    Args:
        count: Residents of the tracts, in persons; finite, >= 0.
        circle_area_m2: Area of the search circle, in square meters (m^2); finite, > 0.
        land_area_m2: Total land area of the tracts, in square meters (m^2); finite, >= 0.
            Zero means the area is unknown and the count is returned unscaled.

    Returns:
        Estimated residents inside the circle, in persons.

    Raises:
        ValueError: If an argument is not finite, is negative, or the circle area is zero.
    """
    _require(count, "count")
    _require(circle_area_m2, "circle_area_m2", positive=True)
    _require(land_area_m2, "land_area_m2")
    if land_area_m2 == 0:
        return float(count)
    return count * min(1.0, circle_area_m2 / land_area_m2)


def _check_counts(total: float, under_5: float, under_18: float, over_65: float) -> None:
    _require(total, "total", positive=True)
    for value, name in ((under_5, "under_5"), (under_18, "under_18"), (over_65, "over_65")):
        _require(value, name)
    if under_5 > under_18:
        raise ValueError("under_5 must not exceed under_18")
    if under_18 + over_65 > total:
        raise ValueError("under_18 plus over_65 must not exceed total")


def age_bands(total: float, under_5: float, under_18: float, over_65: float) -> dict[str, float]:
    """Convert age counts to percent of the total in four bands.

    Args:
        total: All residents, in persons; finite, > 0.
        under_5: Residents under 5 years, in persons; 0 to ``under_18``.
        under_18: Residents under 18 years, in persons; at most ``total - over_65``.
        over_65: Residents 65 years and over, in persons; finite, >= 0.

    Returns:
        Mapping of "0-4", "5-17" (under 18 minus under 5), "18-64" (the remainder) and "65+"
        to percent of ``total`` (0 to 100, two decimals, summing to 100).

    Raises:
        ValueError: If a count is not finite or is negative, the total is not positive, or the
            counts are not nested (under 5 above under 18, or under 18 plus 65 and over above
            the total). Counts are never clipped or adjusted.
    """
    _check_counts(total, under_5, under_18, over_65)
    share = {
        "0-4": round(under_5 / total * _PERCENT, _DECIMALS),
        "5-17": round((under_18 - under_5) / total * _PERCENT, _DECIMALS),
        "65+": round(over_65 / total * _PERCENT, _DECIMALS),
    }
    remainder = max(round(_PERCENT - sum(share.values()), _DECIMALS), 0.0)
    return {"0-4": share["0-4"], "5-17": share["5-17"], "18-64": remainder, "65+": share["65+"]}
