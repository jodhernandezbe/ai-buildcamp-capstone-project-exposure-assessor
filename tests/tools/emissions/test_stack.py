"""Tests for fetch_stack_parameters."""

from __future__ import annotations

import pytest

from tools.emissions.stack import fetch_stack_parameters


def test_schema() -> None:
    assert fetch_stack_parameters.name == "fetch_stack_parameters"
    assert set(fetch_stack_parameters.args) == {"frs_id", "scc_code"}
    assert fetch_stack_parameters.description


def test_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        fetch_stack_parameters.invoke({"frs_id": "x", "scc_code": "y"})
