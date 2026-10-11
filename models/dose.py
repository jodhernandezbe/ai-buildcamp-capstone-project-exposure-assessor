"""Inhalation dose equations."""

from __future__ import annotations

from models._types import FloatOrArray

LIFETIME_DAYS: float = 70.0 * 365.0  # standard 70-year lifetime averaging time, in days


def average_daily_dose(
    c: FloatOrArray, ir: float, ef: float, ed: float, bw: float, at: float
) -> FloatOrArray:
    """Average daily dose, ADD = C * IR * EF * ED / (BW * AT).

    Args:
        c: Exposure concentration in air, in milligrams per cubic meter (mg/m^3).
        ir: Inhalation rate, in cubic meters per day (m^3/day).
        ef: Exposure frequency, in days per year (day/yr).
        ed: Exposure duration, in years (yr).
        bw: Body weight, in kilograms (kg). Must be positive.
        at: Averaging time, in days (day). Must be positive.

    Returns:
        Inhalation dose in milligrams per kilogram per day (mg/(kg*day)).

    Raises:
        ValueError: If ``bw`` or ``at`` is not positive.
    """
    if bw <= 0 or at <= 0:
        raise ValueError("bw and at must be positive")
    return c * ir * ef * ed / (bw * at)


def lifetime_average_daily_dose(
    c: FloatOrArray, ir: float, ef: float, ed: float, bw: float
) -> FloatOrArray:
    """Lifetime average daily dose (LADD): ADD averaged over 70 * 365 days.

    Args:
        c: Exposure concentration in air, in milligrams per cubic meter (mg/m^3).
        ir: Inhalation rate, in cubic meters per day (m^3/day).
        ef: Exposure frequency, in days per year (day/yr).
        ed: Exposure duration, in years (yr).
        bw: Body weight, in kilograms (kg). Must be positive.

    Returns:
        Lifetime-averaged inhalation dose in milligrams per kilogram per day
        (mg/(kg*day)).

    Raises:
        ValueError: If ``bw`` is not positive.
    """
    return average_daily_dose(c, ir, ef, ed, bw, LIFETIME_DAYS)
