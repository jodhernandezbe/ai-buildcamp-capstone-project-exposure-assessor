"""Tests for fetch_chemical_properties."""

from __future__ import annotations

import pytest

from tools.informatics.properties import fetch_chemical_properties


def test_schema() -> None:
    assert fetch_chemical_properties.name == "fetch_chemical_properties"
    assert set(fetch_chemical_properties.args) == {"cas_number"}
    assert fetch_chemical_properties.description


def test_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        fetch_chemical_properties.invoke({"cas_number": "71-43-2"})
