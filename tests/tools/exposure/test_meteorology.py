"""Tests for get_meteorological_boundary."""

from __future__ import annotations

import pytest

from tools.exposure.meteorology import get_meteorological_boundary


def test_schema() -> None:
    assert get_meteorological_boundary.name == "get_meteorological_boundary"
    assert set(get_meteorological_boundary.args) == {"latitude", "longitude"}
    assert get_meteorological_boundary.description


def test_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        get_meteorological_boundary.invoke({"latitude": 0.0, "longitude": 0.0})
