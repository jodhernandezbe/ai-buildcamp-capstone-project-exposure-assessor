"""Inhalation dose equations."""

from __future__ import annotations

from models._types import FloatOrArray

LIFETIME_DAYS: float = 70.0 * 365.0  # standard 70-year lifetime averaging time, in days


def average_daily_dose(
    concentration_mg_per_m3: FloatOrArray,
    inhalation_rate_m3_per_day: float,
    exposure_frequency_days_per_year: float,
    exposure_duration_years: float,
    body_weight_kg: float,
    averaging_time_days: float,
) -> FloatOrArray:
    """Average daily dose, ADD = C * IR * EF * ED / (BW * AT).

    Args:
        concentration_mg_per_m3: Exposure concentration in air, in milligrams per cubic
            meter (mg/m^3).
        inhalation_rate_m3_per_day: Inhalation rate, in cubic meters per day (m^3/day).
        exposure_frequency_days_per_year: Exposure frequency, in days per year (day/yr).
        exposure_duration_years: Exposure duration, in years (yr).
        body_weight_kg: Body weight, in kilograms (kg). Must be positive.
        averaging_time_days: Averaging time, in days (day). Must be positive.

    Returns:
        Inhalation dose in milligrams per kilogram per day (mg/(kg*day)).

    Raises:
        ValueError: If ``body_weight_kg`` or ``averaging_time_days`` is not positive.
    """
    if body_weight_kg <= 0 or averaging_time_days <= 0:
        raise ValueError("body_weight_kg and averaging_time_days must be positive")
    return (
        concentration_mg_per_m3
        * inhalation_rate_m3_per_day
        * exposure_frequency_days_per_year
        * exposure_duration_years
        / (body_weight_kg * averaging_time_days)
    )


def lifetime_average_daily_dose(
    concentration_mg_per_m3: FloatOrArray,
    inhalation_rate_m3_per_day: float,
    exposure_frequency_days_per_year: float,
    exposure_duration_years: float,
    body_weight_kg: float,
) -> FloatOrArray:
    """Lifetime average daily dose (LADD): ADD averaged over 70 * 365 days.

    Args:
        concentration_mg_per_m3: Exposure concentration in air, in milligrams per cubic
            meter (mg/m^3).
        inhalation_rate_m3_per_day: Inhalation rate, in cubic meters per day (m^3/day).
        exposure_frequency_days_per_year: Exposure frequency, in days per year (day/yr).
        exposure_duration_years: Exposure duration, in years (yr).
        body_weight_kg: Body weight, in kilograms (kg). Must be positive.

    Returns:
        Lifetime-averaged inhalation dose in milligrams per kilogram per day
        (mg/(kg*day)).

    Raises:
        ValueError: If ``body_weight_kg`` is not positive.
    """
    return average_daily_dose(
        concentration_mg_per_m3,
        inhalation_rate_m3_per_day,
        exposure_frequency_days_per_year,
        exposure_duration_years,
        body_weight_kg,
        LIFETIME_DAYS,
    )
