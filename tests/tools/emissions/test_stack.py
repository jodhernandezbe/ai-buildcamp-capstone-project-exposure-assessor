"""Tests for the stack parameter tools."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from config.stack import load_stack_settings
from tools.emissions import stack
from tools.emissions.stack import fetch_stack_parameters_from_nei, fetch_stack_parameters_from_scc


def test_nei_schema() -> None:
    assert fetch_stack_parameters_from_nei.name == "fetch_stack_parameters_from_nei"
    assert set(fetch_stack_parameters_from_nei.args) == {"frs_id"}
    assert "fetch_stack_parameters_from_scc" in fetch_stack_parameters_from_nei.description


def test_nei_stub_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        fetch_stack_parameters_from_nei.invoke({"frs_id": "x"})


def test_scc_schema_and_description() -> None:
    tool = fetch_stack_parameters_from_scc
    assert tool.name == "fetch_stack_parameters_from_scc"
    assert set(tool.args) == {"scc_code"}
    description = tool.description
    assert "ONLY after `fetch_stack_parameters_from_nei` returned no values" in description
    assert "not measurements" in description
    for text in ("m above ground", "m/s", "K", '"PSTK"', '"AirToxScreen global default"'):
        assert text in description


def test_scc_tool_uses_configured_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = load_stack_settings()
    missing = replace(settings, pstk=replace(settings.pstk, path=tmp_path / "absent.csv"))
    monkeypatch.setattr(stack, "get_stack_settings", lambda: missing)
    result = fetch_stack_parameters_from_scc.invoke({"scc_code": "99900001"})
    assert result["source"] == "AirToxScreen global default"
    assert result["stack_height"] == settings.global_fallback["stack_height"]


@pytest.mark.parametrize("arguments", [{}, {"scc_code": None}])
def test_scc_tool_without_scc_gives_global_default(arguments: dict[str, object]) -> None:
    settings = load_stack_settings()
    result = fetch_stack_parameters_from_scc.invoke(arguments)
    assert result["source"] == "AirToxScreen global default"
    assert result["scc"] is None
    assert result["exit_temperature"] == settings.global_fallback["exit_temperature"]
    assert "no SCC was given" in result["warnings"][0]


def test_scc_is_optional_in_the_schema() -> None:
    schema = fetch_stack_parameters_from_scc.args["scc_code"]
    assert schema.get("default", "missing") is None
    assert "Omit it" in fetch_stack_parameters_from_scc.description


@pytest.mark.parametrize("code", ["99900001", " 99900001 ", 99900001])
def test_scc_tool_accepts_text_or_number(
    code: str | int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "pstk.csv"
    path.write_text("fips,scc,stkhgt,stkdiam,stkvel,stktemp\n0,99900001,10,1,5,400\n")
    settings = load_stack_settings()
    patched = replace(settings, pstk=replace(settings.pstk, path=path))
    monkeypatch.setattr(stack, "get_stack_settings", lambda: patched)
    result = fetch_stack_parameters_from_scc.invoke({"scc_code": code})
    assert (result["source"], result["scc"], result["stack_height"]) == ("PSTK", "99900001", 10.0)


def test_scc_tool_rejects_a_word() -> None:
    result = fetch_stack_parameters_from_scc.invoke({"scc_code": "abc"})
    assert result["source"] == "AirToxScreen global default"
    assert "is invalid" in result["warnings"][0]
