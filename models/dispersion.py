"""Atmospheric dispersion: Pasquill-Gifford coefficients and the Gaussian plume."""

from __future__ import annotations

import numpy as np

from models._types import FloatOrArray

# Briggs (1973) open-country fits to the Pasquill-Gifford curves, valid for
# 100 m <= x <= 10 km. Each entry: (a, b) for sigma_y = a*x*(1 + 1e-4*x)**-0.5
# and (c, d, e) for sigma_z = c*x*(1 + d*x)**e (d = 0 gives sigma_z = c*x).
_SIGMA_Y_COEFF: dict[str, float] = {
    "A": 0.22,
    "B": 0.16,
    "C": 0.11,
    "D": 0.08,
    "E": 0.06,
    "F": 0.04,
}
_SIGMA_Z_COEFF: dict[str, tuple[float, float, float]] = {
    "A": (0.20, 0.0, 1.0),
    "B": (0.12, 0.0, 1.0),
    "C": (0.08, 0.0002, -0.5),
    "D": (0.06, 0.0015, -0.5),
    "E": (0.03, 0.0003, -1.0),
    "F": (0.016, 0.0003, -1.0),
}


def calculate_dispersion_coefficients(
    downwind_distance_x: FloatOrArray, stability_class: str
) -> tuple[FloatOrArray, FloatOrArray]:
    """Compute Pasquill-Gifford dispersion coefficients (Briggs open-country fits).

    Args:
        downwind_distance_x: Downwind distance from the source, in meters (m).
            Must be positive.
        stability_class: Pasquill-Gifford atmospheric stability class, one of
            "A" (very unstable) through "F" (very stable). Case-insensitive.

    Returns:
        A tuple ``(sigma_y, sigma_z)``: the lateral and vertical plume standard
        deviations, in meters (m), with the same shape as ``downwind_distance_x``.

    Raises:
        ValueError: If ``stability_class`` is not A-F or any distance is not positive.
    """
    cls = stability_class.strip().upper()
    if cls not in _SIGMA_Y_COEFF:
        raise ValueError(f"stability_class must be one of A-F, got {stability_class!r}")
    x = np.asarray(downwind_distance_x, dtype=np.float64)
    if np.any(x <= 0):
        raise ValueError("downwind_distance_x must be positive")

    a = _SIGMA_Y_COEFF[cls]
    c, d, e = _SIGMA_Z_COEFF[cls]
    sigma_y = a * x * (1.0 + 1e-4 * x) ** -0.5
    sigma_z = c * x * (1.0 + d * x) ** e
    if np.ndim(downwind_distance_x) == 0:
        return float(sigma_y), float(sigma_z)
    return sigma_y, sigma_z


def gaussian_plume(
    q: float,
    u: float,
    y: FloatOrArray,
    z: FloatOrArray,
    h: float,
    sigma_y: FloatOrArray,
    sigma_z: FloatOrArray,
) -> FloatOrArray:
    """Steady-state Gaussian plume concentration with ground reflection.

    C = Q / (2 pi u sigma_y sigma_z) * exp(-y^2 / (2 sigma_y^2))
        * [exp(-(z - H)^2 / (2 sigma_z^2)) + exp(-(z + H)^2 / (2 sigma_z^2))]

    Args:
        q: Emission rate, in grams per second (g/s).
        u: Mean wind speed at release height, in meters per second (m/s). Must be positive.
        y: Crosswind distance from the plume centerline, in meters (m).
        z: Receptor height above ground, in meters (m).
        h: Effective release height (stack height plus plume rise), in meters (m).
        sigma_y: Lateral dispersion coefficient, in meters (m). Must be positive.
        sigma_z: Vertical dispersion coefficient, in meters (m). Must be positive.

    Returns:
        Ambient air concentration in grams per cubic meter (g/m^3). Multiply by
        1000 for mg/m^3.

    Raises:
        ValueError: If ``u`` or any sigma is not positive.
    """
    if u <= 0:
        raise ValueError("u must be positive")
    sy = np.asarray(sigma_y, dtype=np.float64)
    sz = np.asarray(sigma_z, dtype=np.float64)
    if np.any(sy <= 0) or np.any(sz <= 0):
        raise ValueError("sigma_y and sigma_z must be positive")
    y_arr = np.asarray(y, dtype=np.float64)
    z_arr = np.asarray(z, dtype=np.float64)

    lateral = np.exp(-(y_arr**2) / (2.0 * sy**2))
    vertical = np.exp(-((z_arr - h) ** 2) / (2.0 * sz**2)) + np.exp(
        -((z_arr + h) ** 2) / (2.0 * sz**2)
    )
    conc = q / (2.0 * np.pi * u * sy * sz) * lateral * vertical
    if np.ndim(conc) == 0:
        return float(conc)
    return np.asarray(conc, dtype=np.float64)
