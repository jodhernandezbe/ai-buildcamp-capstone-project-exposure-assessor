"""Tests for the ``[pubchem]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.loader import get_comptox_settings
from config.parsing import DEFAULT_SETTINGS_PATH, PROJECT_ROOT
from config.pubchem import MIN_DELAY_SECONDS, PubchemSettings, get_pubchem_settings
from config.pubchem import load_pubchem_settings as load_pubchem

SHIPPED = DEFAULT_SETTINGS_PATH.read_text(encoding="utf-8")
SECTION_START = SHIPPED.index("[pubchem]\n")
SECTION_END = SHIPPED.index("# Source unit spellings")
PUBCHEM_TEXT = SHIPPED[SECTION_START:SECTION_END]
COMPTOX_TEXT = SHIPPED[: SHIPPED.index("# EPA Envirofacts (efservice)")]


def _load(tmp_path: Path, pubchem: str = PUBCHEM_TEXT) -> PubchemSettings:
    path = tmp_path / "settings.toml"
    path.write_text(COMPTOX_TEXT + pubchem, encoding="utf-8")
    return load_pubchem(path)


def _bad(tmp_path: Path, old: str, new: str, message: str) -> None:
    assert old in PUBCHEM_TEXT
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, PUBCHEM_TEXT.replace(old, new, 1))


def test_shipped_settings_load() -> None:
    settings = get_pubchem_settings()
    assert [spec.key for spec in settings.fields] == [
        "molecular_weight",
        "vapor_pressure",
        "density",
    ]
    assert settings.delay_seconds >= MIN_DELAY_SECONDS
    assert settings.cache.path == PROJECT_ROOT / ".cache/pubchem/responses.sqlite"


def test_toxicity_values_are_not_requested_from_pubchem() -> None:
    keys = {spec.key for spec in get_pubchem_settings().fields}
    assert keys.isdisjoint({"rfd", "rfc", "sf", "iur"})


def test_target_units_match_comptox() -> None:
    comptox = get_comptox_settings()
    units = {p.key: p.target_unit for p in comptox.properties}
    units["molecular_weight"] = comptox.molecular_weight.target_unit
    for spec in get_pubchem_settings().fields:
        assert spec.target_unit == units[spec.key]


def test_urls_are_encoded() -> None:
    settings = get_pubchem_settings()
    assert settings.smiles_url("C/C#N").endswith("/smiles/C%2FC%23N/cids/JSON")
    assert settings.name_url("106-97-8").endswith("/name/106-97-8/cids/JSON")
    assert settings.record_url(7843).endswith("/data/compound/7843/JSON")


def test_field_temperature_window(tmp_path: Path) -> None:
    pressure = {s.key: s for s in _load(tmp_path).fields}["vapor_pressure"]
    assert (pressure.min_celsius, pressure.max_celsius) == (20.0, 25.0)
    assert pressure.allow_missing_temperature is False


def test_delay_below_pubchem_limit_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, "delay_seconds = 0.25", "delay_seconds = 0.1", "at least 0.2")


@pytest.mark.parametrize("key", ["cid_by_smiles_url", "cid_by_name_url", "pug_view_url"])
def test_template_without_its_slot_is_rejected(tmp_path: Path, key: str) -> None:
    line = next(x for x in PUBCHEM_TEXT.splitlines() if x.startswith(f"{key} ="))
    _bad(tmp_path, line, f'{key} = "https://example.test/x"', key)


def test_template_with_another_slot_is_rejected(tmp_path: Path) -> None:
    old = "data/compound/{cid}/JSON"
    _bad(tmp_path, old, "data/compound/{cid}/{other}", "pug_view_url")


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("timeout_seconds = 30.0", "timeout_seconds = 0", "timeout_seconds"),
        ("timeout_seconds = 30.0", "timeout_seconds = true", "timeout_seconds"),
        ("max_retries = 2", "max_retries = -1", "max_retries"),
        ("agreement_ratio = 2.0", "agreement_ratio = 0.5", "agreement_ratio"),
        ("ttl_days = 30", "ttl_days = 0", "ttl_days"),
        ("enabled = true", "enabled = 1", "enabled"),
        ('user_agent = "', 'user_agent = "" #', "user_agent"),
    ],
)
def test_invalid_numbers_are_rejected(tmp_path: Path, old: str, new: str, message: str) -> None:
    _bad(tmp_path, old, new, message)


def test_half_a_temperature_window_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, "min_celsius = 20.0\n", "", "min_celsius and max_celsius")


def test_inverted_temperature_window_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, "min_celsius = 20.0", "min_celsius = 30.0", "min below max")


def test_unit_different_from_comptox_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, 'target_unit = "mmHg"', 'target_unit = "Pa"', "must equal the CompTox one")


def test_field_that_is_not_a_result_field_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, 'key = "density"', 'key = "colour"', "not a numeric property")


def test_toxicity_key_is_rejected_until_it_is_a_numeric_property(tmp_path: Path) -> None:
    _bad(tmp_path, 'key = "density"', 'key = "rfc"', "not a numeric property")


def test_duplicate_field_is_rejected(tmp_path: Path) -> None:
    _bad(tmp_path, 'key = "density"', 'key = "vapor_pressure"', "listed twice")


def test_no_fields_is_rejected(tmp_path: Path) -> None:
    text = PUBCHEM_TEXT[: PUBCHEM_TEXT.index("[[pubchem.fields]]")]
    with pytest.raises(ValueError, match="fields"):
        _load(tmp_path, text)


def test_empty_heading_is_rejected(tmp_path: Path) -> None:
    _bad(
        tmp_path,
        'cas_heading = ["Names and Identifiers", "Other Identifiers", "CAS"]',
        "cas_heading = []",
        "cas_heading",
    )


def test_missing_section_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(COMPTOX_TEXT, encoding="utf-8")
    with pytest.raises(ValueError, match="pubchem section is missing"):
        load_pubchem(path)
