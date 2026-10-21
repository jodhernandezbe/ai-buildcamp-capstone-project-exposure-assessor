"""The drawn circle and sector are placed where the bearings say, at the radius given."""

from __future__ import annotations

import math

import pytest

from api.services.geometry import EARTH_RADIUS_KM, circle, destination, sector

LAT, LON = 10.0, -20.0  # synthetic centre


def distance_km(first: list[float], second: list[float]) -> float:
    """Great-circle (haversine) distance between two ``[lon, lat]`` positions."""
    (lon1, lat1), (lon2, lat2) = first, second
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bearing_deg(origin: list[float], target: list[float]) -> float:
    (lon1, lat1), (lon2, lat2) = origin, target
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


@pytest.mark.parametrize("bearing", [0.0, 90.0, 180.0, 270.0, 45.0])
def test_a_destination_is_the_distance_away_on_the_bearing(bearing: float) -> None:
    there = destination(LAT, LON, bearing, 5.0)
    assert distance_km([LON, LAT], there) == pytest.approx(5.0, rel=1e-6)
    assert bearing_deg([LON, LAT], there) == pytest.approx(bearing, abs=1e-6)


def test_north_raises_the_latitude_and_east_the_longitude() -> None:
    assert destination(LAT, LON, 0.0, 5.0)[1] > LAT
    assert destination(LAT, LON, 90.0, 5.0)[0] > LON


def test_the_circle_is_a_closed_ring_at_the_radius() -> None:
    ring = circle(LAT, LON, 3.0, 10.0).coordinates[0]
    assert ring[0] == pytest.approx(ring[-1])
    assert len(ring) == 37
    assert all(distance_km([LON, LAT], p) == pytest.approx(3.0, rel=1e-6) for p in ring)


def test_the_circle_runs_counter_clockwise() -> None:
    ring = circle(LAT, LON, 3.0, 10.0).coordinates[0]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:], strict=False))
    assert area > 0


def test_wind_from_the_west_gives_a_sector_toward_the_east() -> None:
    wedge = sector(LAT, LON, (270.0 + 180) % 360, 3.0, 20.0, 10.0).coordinates[0]
    arc = wedge[1:-1]
    middle = arc[len(arc) // 2]
    assert bearing_deg([LON, LAT], middle) == pytest.approx(90.0, abs=1e-6)
    assert middle[0] > LON


def test_the_sector_starts_and_ends_at_the_centre_and_spans_the_half_angle() -> None:
    wedge = sector(LAT, LON, 90.0, 3.0, 20.0, 10.0).coordinates[0]
    assert wedge[0] == wedge[-1] == [LON, LAT]
    bearings = [bearing_deg([LON, LAT], p) for p in wedge[1:-1]]
    assert max(bearings) == pytest.approx(110.0, abs=1e-6)
    assert min(bearings) == pytest.approx(70.0, abs=1e-6)
    assert all(distance_km([LON, LAT], p) == pytest.approx(3.0, rel=1e-6) for p in wedge[1:-1])


def test_a_sector_pointing_north_spans_across_the_zero_bearing() -> None:
    wedge = sector(LAT, LON, 0.0, 3.0, 20.0, 10.0).coordinates[0]
    lons = [p[0] for p in wedge[1:-1]]
    assert min(lons) < LON < max(lons)
    assert all(p[1] > LAT for p in wedge[1:-1])


def test_a_coarse_spacing_still_draws_both_edges() -> None:
    wedge = sector(LAT, LON, 90.0, 3.0, 20.0, 90.0).coordinates[0]
    assert len(wedge[1:-1]) >= 2


def test_longitudes_stay_within_the_valid_range() -> None:
    assert -180.0 <= destination(0.0, 179.99, 90.0, 50.0)[0] <= 180.0
