"""Tests for get_facility_metadata."""

from __future__ import annotations

import pytest

from tools.geospatial.metadata import get_facility_metadata


def test_schema() -> None:
    assert get_facility_metadata.name == "get_facility_metadata"
    assert set(get_facility_metadata.args) == {"frs_id"}
    assert get_facility_metadata.description


def test_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        get_facility_metadata.invoke({"frs_id": "x"})
