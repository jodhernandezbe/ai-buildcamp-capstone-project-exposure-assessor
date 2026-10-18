"""Tests for models.transport.dispersion."""

from __future__ import annotations

import math

import numpy as np
import pytest

from models.transport.dispersion import calculate_dispersion_coefficients, gaussian_plume


def test_class_d_at_1km() -> None:
    sy, sz = calculate_dispersion_coefficients(1000.0, "d")
    assert sy == pytest.approx(0.08 * 1000 * (1.1) ** -0.5)
    assert sz == pytest.approx(0.06 * 1000 * (1 + 1.5) ** -0.5)


def test_stability_ordering() -> None:
    sz_a = calculate_dispersion_coefficients(500.0, "A")[1]
    sz_f = calculate_dispersion_coefficients(500.0, "F")[1]
    assert sz_a > sz_f


def test_array_input() -> None:
    sy, sz = calculate_dispersion_coefficients(np.array([100.0, 1000.0]), "C")
    assert isinstance(sy, np.ndarray) and sy.shape == (2,)
    assert isinstance(sz, np.ndarray) and sz[1] > sz[0]


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        calculate_dispersion_coefficients(100.0, "G")
    with pytest.raises(ValueError):
        calculate_dispersion_coefficients(0.0, "A")


def test_plume_centerline_ground_level() -> None:
    q, u, sy, sz = 10.0, 5.0, 20.0, 10.0
    # z = 0, y = 0, h = 0: reflection doubles the single-lobe value.
    expected = 2 * q / (2 * math.pi * u * sy * sz)
    assert gaussian_plume(q, u, 0.0, 0.0, 0.0, sy, sz) == pytest.approx(expected)


def test_plume_decays_off_axis() -> None:
    on = gaussian_plume(10.0, 5.0, 0.0, 0.0, 10.0, 20.0, 10.0)
    off = gaussian_plume(10.0, 5.0, 50.0, 0.0, 10.0, 20.0, 10.0)
    assert isinstance(on, float) and isinstance(off, float)
    assert off < on


def test_plume_array_and_validation() -> None:
    out = gaussian_plume(1.0, 2.0, np.array([0.0, 10.0]), 1.5, 5.0, 10.0, 5.0)
    assert isinstance(out, np.ndarray) and out.shape == (2,)
    with pytest.raises(ValueError):
        gaussian_plume(1.0, 0.0, 0.0, 0.0, 5.0, 10.0, 5.0)
