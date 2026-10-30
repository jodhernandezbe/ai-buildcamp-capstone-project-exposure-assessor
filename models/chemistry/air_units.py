"""Gas concentration unit conversion for air."""

from __future__ import annotations

import math


def ppm_to_mg_per_m3(ppm: float, molecular_weight: float, molar_volume_l_per_mol: float) -> float:
    """Convert a gas concentration in ppm (by volume) to mg/m^3.

    C = ppm x MW / V_m, with V_m the molar volume of an ideal gas (24.45 L/mol at 25 degC and
    1 atm).

    Args:
        ppm: Concentration, parts per million by volume; >= 0.
        molecular_weight: Molecular weight MW, g/mol; > 0.
        molar_volume_l_per_mol: Molar volume V_m, L/mol; > 0.

    Returns:
        Concentration, mg/m^3.

    Raises:
        ValueError: If an input is not finite, ppm is negative or MW or V_m is not positive.
    """
    for name, value in (
        ("ppm", ppm),
        ("molecular_weight", molecular_weight),
        ("molar_volume_l_per_mol", molar_volume_l_per_mol),
    ):
        if isinstance(value, bool) or not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number, got {value!r}")
    if ppm < 0 or molecular_weight <= 0 or molar_volume_l_per_mol <= 0:
        raise ValueError("ppm must be >= 0 and the molecular weight and molar volume > 0")
    return ppm * molecular_weight / molar_volume_l_per_mol
