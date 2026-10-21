"""Tests for the ``[ui]`` settings loader (web backend and display settings)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from config.ui import get_ui_settings, load_ui_settings
from tools.registry import get_all_tools

UI = """
[ui]
host = "127.0.0.1"
port = 9000
frontend_dist = "frontend/dist"
max_key_length = 64

[ui.keyring]
service = "svc"

[ui.keyring.accounts]
openai = "acct-openai"
census = "acct-census"
comptox = "acct-comptox"

[ui.prompts]
scope_classifier = "classifier"
scope_addendum = "addendum"
scope_fallback = "fallback"
history_window = 4

[ui.step_labels]
some_tool = "Did a thing"

[ui.map]
light_style = "https://example.test/light.json"
dark_style = "https://example.test/dark.json"
sector_half_angle_deg = 20.0
vertex_spacing_deg = 10.0
marker_min_px = 4.0
marker_max_px = 10.0
coordinate_tolerance_deg = 0.001

[ui.map.initial_view]
west = -10.0
south = 20.0
east = 10.0
north = 30.0

[ui.thresholds]
hq_concern = 1.0
hq_near_lower = 0.2
cancer_lower = 0.01
cancer_upper = 0.1

[ui.display]
significant_digits = 2
narrow_breakpoint_px = 800
suggestions = ["first", "second"]

[ui.pricing."model-a"]
input_usd_per_mtok = 1.5
cached_input_usd_per_mtok = 0.5
output_usd_per_mtok = 3.0
priced_on = 2026-01-02
source_url = "https://example.test/pricing"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


def _replace(tmp_path: Path, line_start: str, new_line: str) -> Path:
    lines = [new_line if ln.startswith(line_start) else ln for ln in UI.splitlines()]
    return _write(tmp_path, "\n".join(lines))


def test_values(tmp_path: Path) -> None:
    settings = load_ui_settings(_write(tmp_path, UI))
    assert (settings.host, settings.port, settings.origin) == (
        "127.0.0.1",
        9000,
        "http://127.0.0.1:9000",
    )
    assert settings.frontend_dist.is_absolute()
    assert settings.keyring.service == "svc"
    assert dict(settings.keyring.accounts) == {
        "openai": "acct-openai",
        "census": "acct-census",
        "comptox": "acct-comptox",
    }
    assert settings.prompts.history_window == 4
    assert dict(settings.step_labels) == {"some_tool": "Did a thing"}
    assert settings.map.sector_half_angle_deg == 20.0
    assert settings.map.vertex_spacing_deg == 10.0
    view = settings.map.initial_view
    assert (view.west, view.south, view.east, view.north) == (-10.0, 20.0, 10.0, 30.0)
    assert settings.thresholds.hq_near_lower == 0.2
    assert settings.display.suggestions == ("first", "second")
    price = settings.pricing["model-a"]
    assert (price.input_usd_per_mtok, price.priced_on) == (1.5, date(2026, 1, 2))


def test_shipped_settings_load() -> None:
    settings = get_ui_settings()
    assert settings.keyring.service == "epa-chemical-risk-agent"
    assert dict(settings.keyring.accounts) == {
        "openai": "openai_api_key",
        "census": "census_api_key",
        "comptox": "comptox_api_key",
    }
    assert settings.thresholds.hq_concern == 1.0
    assert 3 <= len(settings.display.suggestions) <= 4


def test_shipped_price_of_the_configured_model_is_sourced() -> None:
    price = get_ui_settings().pricing["gpt-4.1"]
    assert (price.input_usd_per_mtok, price.output_usd_per_mtok) == (2.0, 8.0)
    assert 0 < price.cached_input_usd_per_mtok < price.input_usd_per_mtok
    assert price.source_url.startswith("https://platform.openai.com/")
    assert price.priced_on == date(2026, 10, 20)


def test_shipped_step_labels_name_registered_tools() -> None:
    registered = {tool.name for tool in get_all_tools()}
    assert set(get_ui_settings().step_labels) == registered


def test_localhost_accepted(tmp_path: Path) -> None:
    path = _replace(tmp_path, "host", 'host = "localhost"')
    assert load_ui_settings(path).host == "localhost"


def test_unpriced_when_pricing_empty(tmp_path: Path) -> None:
    text = UI.split('[ui.pricing."model-a"]')[0] + "[ui.pricing]\n"
    assert dict(load_ui_settings(_write(tmp_path, text)).pricing) == {}


@pytest.mark.parametrize(
    ("line_start", "new_line", "key"),
    [
        ("host", 'host = "0.0.0.0"', "ui.host"),
        ("host", 'host = "example.com"', "ui.host"),
        ("port", "port = 0", "ui.port"),
        ("port", "port = 70000", "ui.port"),
        ("port", "port = true", "ui.port"),
        ("max_key_length", "max_key_length = 0", "ui.max_key_length"),
        ("service", 'service = " "', "ui.keyring.service"),
        ("census", 'census = ""', "ui.keyring.accounts.census"),
        ("comptox", 'comptox = "acct-openai"', "own account name"),
        ("openai", "openai = 5", "ui.keyring.accounts.openai"),
        ("scope_classifier", 'scope_classifier = ""', "ui.prompts.scope_classifier"),
        ("history_window", "history_window = -1", "ui.prompts.history_window"),
        ("some_tool", "some_tool = 3", "ui.step_labels.some_tool"),
        ("sector_half_angle_deg", "sector_half_angle_deg = 90", "sector_half_angle_deg"),
        ("vertex_spacing_deg", "vertex_spacing_deg = 0.01", "ui.map.vertex_spacing_deg"),
        ("vertex_spacing_deg", "vertex_spacing_deg = 91", "vertex_spacing_deg"),
        ("west", "west = 10.0", "west < east"),
        ("north", "north = 20.0", "south < north"),
        ("north", "north = 91.0", "ui.map.initial_view.north"),
        ("west", "west = -181.0", "ui.map.initial_view.west"),
        ("south", "south = true", "ui.map.initial_view.south"),
        ("marker_max_px", "marker_max_px = 1.0", "ui.map.marker_max_px"),
        ("coordinate_tolerance_deg", "coordinate_tolerance_deg = -1", "coordinate_tolerance"),
        ("hq_concern", "hq_concern = true", "ui.thresholds.hq_concern"),
        ("hq_near_lower", "hq_near_lower = 2.0", "ui.thresholds.hq_near_lower"),
        ("hq_near_lower", "hq_near_lower = -0.1", "ui.thresholds.hq_near_lower"),
        ("cancer_lower", "cancer_lower = 0.5", "ui.thresholds.cancer_lower"),
        ("significant_digits", "significant_digits = 0", "ui.display.significant_digits"),
        ("suggestions", "suggestions = []", "ui.display.suggestions"),
        ("input_usd_per_mtok", "input_usd_per_mtok = -1", "input_usd_per_mtok"),
        ("output_usd_per_mtok", "output_usd_per_mtok = true", "output_usd_per_mtok"),
        ("cached_input_usd_per_mtok", 'cached_input_usd_per_mtok = "1"', "cached_input"),
        ("priced_on", 'priced_on = "2026-01-02"', "priced_on"),
        ("source_url", 'source_url = ""', "source_url"),
    ],
)
def test_invalid_entry(tmp_path: Path, line_start: str, new_line: str, key: str) -> None:
    with pytest.raises(ValueError, match=key):
        load_ui_settings(_replace(tmp_path, line_start, new_line))


def test_missing_section(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ui section is missing"):
        load_ui_settings(_write(tmp_path, "[agent]\n"))
