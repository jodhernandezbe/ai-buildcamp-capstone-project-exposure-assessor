"""Tests for config.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.loader import load_settings

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
