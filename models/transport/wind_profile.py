"""Wind speed at release height from the 10 m wind: the power law of EPA's screening procedures.

Source: EPA-454/R-92-019, section 3 (equation 3.1 and Table 3-1): u(z) = u_ref (z / z_ref)^p,
valid from about 10 to 300 m; below 10 m the reference wind is used without adjustment.
"""

from __future__ import annotations

import math

REFERENCE_HEIGHT_M = 10.0


def wind_speed_at_height(
    wind_speed_10m_m_per_s: float,
    height_m: float,
    exponent: float,
) -> float:
    """Adjust a 10 m wind speed to a release height with the power law.

    Args:
        wind_speed_10m_m_per_s: Wind speed at 10 m, in meters per second (m/s); > 0.
        height_m: Release height above ground, in meters (m); >= 0. Below 10 m the 10 m wind
            is returned unchanged.
        exponent: Stability-dependent power-law exponent (unitless); >= 0.

    Returns:
        Wind speed at ``height_m`` in meters per second (m/s).

    Raises:
        ValueError: If a value is not finite, the wind speed is not positive, or the height or
            exponent is negative.
    """
    for value, name in (
        (wind_speed_10m_m_per_s, "wind_speed_10m_m_per_s"),
        (height_m, "height_m"),
        (exponent, "exponent"),
    ):
        if isinstance(value, bool) or not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number, got {value!r}")
    if wind_speed_10m_m_per_s <= 0:
        raise ValueError("wind_speed_10m_m_per_s must be positive")
    if height_m < 0 or exponent < 0:
        raise ValueError("height_m and exponent must be non-negative")
    if height_m < REFERENCE_HEIGHT_M:
        return wind_speed_10m_m_per_s
    return wind_speed_10m_m_per_s * (height_m / REFERENCE_HEIGHT_M) ** exponent
