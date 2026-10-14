"""Tests for config.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.loader import load_comptox_settings, load_settings

VALID = """
[pubchem]
base_url = "https://example.test/pug/"
compound_property_path = "/x/{identifier}/y"
delay_seconds = 0
timeout_seconds = 3
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


def test_default_file_loads() -> None:
    settings = load_settings()
    assert "{identifier}" in settings.compound_property_url
    assert settings.base_url.startswith("https://")


def test_explicit_path(tmp_path: Path) -> None:
    settings = load_settings(_write(tmp_path, VALID))
    assert settings.compound_property_url == "https://example.test/pug/x/{identifier}/y"
    assert settings.delay_seconds == 0.0
    assert settings.timeout_seconds == 3.0


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nope.toml"):
        load_settings(tmp_path / "nope.toml")


def test_missing_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pubchem.base_url"):
        load_settings(_write(tmp_path, VALID.replace("base_url", "other")))


def test_negative_delay(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pubchem.delay_seconds"):
        load_settings(_write(tmp_path, VALID.replace("delay_seconds = 0", "delay_seconds = -1")))


def test_non_numeric_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pubchem.timeout_seconds"):
        load_settings(
            _write(tmp_path, VALID.replace("timeout_seconds = 3", 'timeout_seconds = "x"'))
        )


def test_template_requires_placeholder(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="identifier"):
        load_settings(_write(tmp_path, VALID.replace("{identifier}", "abc")))


COMPTOX = """
[comptox]
base_url = "https://ctx.test/api/"
dtxsid_by_smiles_path = "/s?smiles={smiles}"
properties_by_dtxsid_path = "/p/{dtxsid}"
api_key_header = "x-key"  # pragma: allowlist secret
api_key_env_var = "SOME_KEY_VAR"  # pragma: allowlist secret
delay_seconds = 0
timeout_seconds = 2

[[comptox.properties]]
key = "a"
name = "Prop A"

[[comptox.properties]]
key = "b"
name = "Prop B"
"""


def test_comptox_default_file_loads() -> None:
    settings = load_comptox_settings()
    assert {spec.key for spec in settings.properties} >= {"vapor_pressure", "density"}
    assert "{smiles}" in settings.dtxsid_by_smiles_url
    assert "{dtxsid}" in settings.properties_by_dtxsid_url
    assert settings.api_key_env_var


def test_comptox_explicit_path(tmp_path: Path) -> None:
    settings = load_comptox_settings(_write(tmp_path, COMPTOX))
    assert settings.dtxsid_by_smiles_url == "https://ctx.test/api/s?smiles={smiles}"
    assert settings.properties_by_dtxsid_url == "https://ctx.test/api/p/{dtxsid}"
    assert [(p.key, p.name) for p in settings.properties] == [("a", "Prop A"), ("b", "Prop B")]
    assert settings.timeout_seconds == 2.0


def test_comptox_missing_section(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="comptox section"):
        load_comptox_settings(_write(tmp_path, VALID))


def test_comptox_missing_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="comptox.api_key_env_var"):
        load_comptox_settings(_write(tmp_path, COMPTOX.replace("api_key_env_var", "other")))


def test_comptox_bad_placeholders(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="smiles"):
        load_comptox_settings(_write(tmp_path, COMPTOX.replace("{smiles}", "x")))
    with pytest.raises(ValueError, match="dtxsid"):
        load_comptox_settings(_write(tmp_path, COMPTOX.replace("{dtxsid}", "x")))


def test_comptox_duplicate_property_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unique"):
        load_comptox_settings(_write(tmp_path, COMPTOX.replace('key = "b"', 'key = "a"')))


def test_comptox_requires_properties(tmp_path: Path) -> None:
    head = COMPTOX.split("[[comptox.properties]]")[0]
    with pytest.raises(ValueError, match="comptox.properties"):
        load_comptox_settings(_write(tmp_path, head))


def test_comptox_negative_delay(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="comptox.delay_seconds"):
        load_comptox_settings(
            _write(tmp_path, COMPTOX.replace("delay_seconds = 0", "delay_seconds = -1"))
        )
