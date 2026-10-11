"""Emission-rate conversion and risk characterization ratios."""

from __future__ import annotations

_G_PER_KG: float = 1000.0
_S_PER_HOUR: float = 3600.0


def calculate_emission_rate(annual_mass_kg: float, operating_hours: float = 8760.0) -> float:
    """Convert an annual release mass to a steady-state emission rate.

    Args:
        annual_mass_kg: Mass released per year, in kilograms per year (kg/yr).
            Must be non-negative.
        operating_hours: Hours per year the source operates, in hours (hr).
            Defaults to 8760 (continuous operation).

    Returns:
        Emission rate Q in grams per second (g/s).

    Raises:
        ValueError: If ``annual_mass_kg`` is negative or ``operating_hours`` is not positive.
    """
    if annual_mass_kg < 0:
        raise ValueError("annual_mass_kg must be non-negative")
    if operating_hours <= 0:
        raise ValueError("operating_hours must be positive")
    return annual_mass_kg * _G_PER_KG / (operating_hours * _S_PER_HOUR)


def calculate_hazard_quotient(dose_or_conc: float, benchmark: float) -> float:
    """Non-carcinogenic screening ratio: HQ = ADD / RfD or HQ = C / RfC.

    Args:
        dose_or_conc: Average daily dose in mg/(kg*day), or air concentration in
            mg/m^3. Must match the units of ``benchmark``.
        benchmark: Reference dose RfD in mg/(kg*day), or reference concentration
            RfC in mg/m^3. Must be positive.

    Returns:
        Unitless hazard quotient. Values above 1 indicate potential concern.

    Raises:
        ValueError: If ``benchmark`` is not positive.
    """
    if benchmark <= 0:
        raise ValueError("benchmark must be positive")
    return dose_or_conc / benchmark


def calculate_cancer_risk(dose_or_conc: float, slope_factor_or_iur: float) -> float:
    """Upper-bound lifetime excess cancer risk: CR = LADD * SF or CR = C * IUR.

    Args:
        dose_or_conc: Lifetime average daily dose in mg/(kg*day), or air
            concentration in ug/m^3 (when using an IUR).
        slope_factor_or_iur: Slope factor SF in (mg/(kg*day))^-1, or inhalation
            unit risk IUR in (ug/m^3)^-1. Must pair with ``dose_or_conc`` units.
            Must be non-negative.

    Returns:
        Unitless probability of excess lifetime cancer (e.g. 1e-6 is one in a million).

    Raises:
        ValueError: If ``slope_factor_or_iur`` is negative.
    """
    if slope_factor_or_iur < 0:
        raise ValueError("slope_factor_or_iur must be non-negative")
    return dose_or_conc * slope_factor_or_iur
