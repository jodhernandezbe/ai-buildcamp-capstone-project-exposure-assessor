"""Pasquill-Gifford stability class of one hour, from EPA's classification keys.

Source: U.S. EPA (2000), Meteorological Monitoring Guidance for Regulatory Modeling
Applications, EPA-454/R-99-005, section 6.4.

- Daytime: the solar radiation/delta-T (SRDT) key, Table 6-7, which uses total solar
  radiation and the 10 m wind speed in place of cloud and ceiling observations.
- Night: SRDT's night key needs a 10 m minus 2 m temperature difference, which is not
  available here, so nights use Turner's key (Tables 6-4 and 6-6): net radiation index -1 when
  total cloud cover exceeds 4/10 and -2 otherwise. Turner's classes 6 and 7 are combined as F,
  as EPA does for regulatory modeling.
- Turner's rule that total overcast with a ceiling below 7,000 ft gives class D, day or night,
  is applied as low cloud cover (below 2 km) of 100 percent.
"""

from __future__ import annotations

import math

# SRDT daytime key: radiation columns (W/m^2), lower bounds from strongest to weakest.
_DAY_RADIATION_FLOORS: tuple[float, ...] = (925.0, 675.0, 175.0)
# Rows: (upper wind speed bound in m/s, class per radiation column >=925, 675-925,
# 175-675, <175).
_DAY_KEY: tuple[tuple[float, str], ...] = (
    (2.0, "AABD"),
    (3.0, "ABCD"),
    (5.0, "BBCD"),
    (6.0, "CCDD"),
    (math.inf, "CDDD"),
)
# Turner night key: (upper wind speed bound in m/s, class).
_NIGHT_CLOUDY: tuple[tuple[float, str], ...] = ((1.9, "F"), (3.4, "E"), (math.inf, "D"))
_NIGHT_CLEAR: tuple[tuple[float, str], ...] = ((3.4, "F"), (5.5, "E"), (math.inf, "D"))
_CLOUDY_NIGHT_ABOVE_PERCENT = 40.0
_LOW_OVERCAST_PERCENT = 100.0
_NEUTRAL = "D"


def _check(value: float, name: str, maximum: float = math.inf) -> None:
    if isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be a finite number from 0 to {maximum:g}, got {value!r}")


def _by_wind(key: tuple[tuple[float, str], ...], wind_speed: float) -> str:
    return next(cls for bound, cls in key if wind_speed < bound)


def _radiation_column(solar_radiation: float) -> int:
    for column, floor in enumerate(_DAY_RADIATION_FLOORS):
        if solar_radiation >= floor:
            return column
    return len(_DAY_RADIATION_FLOORS)


def _daytime(wind_speed: float, solar_radiation: float) -> str:
    row = _by_wind(_DAY_KEY, wind_speed)
    return row[_radiation_column(solar_radiation)]


def _night(wind_speed: float, cloud_cover: float) -> str:
    cloudy = cloud_cover > _CLOUDY_NIGHT_ABOVE_PERCENT
    return _by_wind(_NIGHT_CLOUDY if cloudy else _NIGHT_CLEAR, wind_speed)


def classify_stability(
    wind_speed: float,
    solar_radiation: float,
    cloud_cover: float,
    low_cloud_cover: float,
    is_day: bool,
) -> str:
    """Return the Pasquill-Gifford stability class of one hour.

    Args:
        wind_speed: Wind speed at 10 m, in meters per second (m/s); finite, >= 0.
        solar_radiation: Total (global horizontal) solar radiation, in watts per square
            meter (W/m^2); finite, >= 0.
        cloud_cover: Total cloud cover, in percent (%), 0 to 100.
        low_cloud_cover: Cloud cover below about 2 km, in percent (%), 0 to 100.
        is_day: True for a daytime hour.

    Returns:
        A class from "A" (very unstable) to "F" (stable).

    Raises:
        ValueError: If a value is not finite or is outside its range.
    """
    _check(wind_speed, "wind_speed")
    _check(solar_radiation, "solar_radiation")
    _check(cloud_cover, "cloud_cover", 100.0)
    _check(low_cloud_cover, "low_cloud_cover", 100.0)
    if low_cloud_cover >= _LOW_OVERCAST_PERCENT:
        return _NEUTRAL
    if is_day:
        return _daytime(wind_speed, solar_radiation)
    return _night(wind_speed, cloud_cover)
