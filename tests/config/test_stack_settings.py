"""Tests for the ``[stack]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.parsing import PROJECT_ROOT
from config.stack import STACK_QUANTITIES, StackSettings, load_stack_settings

PSTK = """
[stack.pstk]
path = "fixtures/pstk.csv"
scc_column = "code"
fips_column = "region"
national_fips = ["0"]

[stack.pstk.columns]
stack_height = "h"
stack_diameter = "d"
exit_velocity = "v"
exit_temperature = "t"

[stack.pstk.units]
stack_height = "ft"
stack_diameter = "ft"
exit_velocity = "ft/s"
exit_temperature = "degF"
"""

NEI = """
[stack.nei]
directory = "fixtures/nei"
file_template = "n_{prefix}.csv.gz"
prefix_digits = 2
id_column = "eis"
max_candidates = 3
merge_significant_digits = 4
raw_path = "fixtures/raw.zip"
raw_id_column = "FAC"

[stack.nei.columns]
stack_height = "h"
stack_diameter = "d"
exit_velocity = "v"
exit_temperature = "t"

[stack.nei.units]
stack_height = "ft"
stack_diameter = "ft"
exit_velocity = "ft/s"
exit_temperature = "degF"

[stack.nei.raw_columns]
stack_height = "H"
stack_diameter = "D"
exit_velocity = "V"
exit_temperature = "T"
"""

REST = """
[stack.target_units]
stack_height = "m"
stack_diameter = "m"
exit_velocity = "m/s"
exit_temperature = "K"

[stack.ranges]
stack_height = [0.1, 450.0]
stack_diameter = [0.01, 30.0]
exit_velocity = [0.01, 150.0]
exit_temperature = [200.0, 1800.0]

[stack.global_fallback]
stack_height = 3.0
stack_diameter = 0.2
exit_velocity = 4.0
exit_temperature = 295.4
"""


def _load(tmp_path: Path, text: str) -> StackSettings:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return load_stack_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    settings = _load(tmp_path, PSTK + NEI + REST)
    assert settings.pstk.path == PROJECT_ROOT / "fixtures/pstk.csv"
    assert settings.pstk.scc_column == "code"
    assert settings.pstk.fips_column == "region"
    assert settings.pstk.national_fips == ("0",)
    assert settings.pstk.units["exit_temperature"] == "degF"
    assert settings.ranges["stack_height"].maximum == 450.0
    assert dict(settings.global_fallback) == {
        "stack_height": 3.0,
        "stack_diameter": 0.2,
        "exit_velocity": 4.0,
        "exit_temperature": 295.4,
    }


def test_default_file_has_airtoxscreen_fallback() -> None:
    settings = load_stack_settings()
    assert tuple(settings.global_fallback) == STACK_QUANTITIES
    assert settings.global_fallback["exit_temperature"] == 295.4
    assert settings.target_units["exit_velocity"] == "m/s"


def test_absolute_path_kept(tmp_path: Path) -> None:
    text = PSTK.replace('"fixtures/pstk.csv"', f'"{tmp_path / "p.csv"}"') + NEI + REST
    assert _load(tmp_path, text).pstk.path == tmp_path / "p.csv"


def test_fips_column_optional(tmp_path: Path) -> None:
    text = PSTK.replace('fips_column = "region"\n', "") + NEI + REST
    assert _load(tmp_path, text).pstk.fips_column is None


def test_settings_are_immutable(tmp_path: Path) -> None:
    settings = _load(tmp_path, PSTK + NEI + REST)
    with pytest.raises(TypeError):
        settings.global_fallback["stack_height"] = 1.0  # type: ignore[index]


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("stack_height = 3.0", "stack_height = 0.0", "global_fallback.stack_height"),
        ("stack_height = 3.0", "stack_height = -3.0", "global_fallback.stack_height"),
        ("stack_height = 3.0", "stack_height = true", "global_fallback.stack_height"),
        ("stack_height = 3.0", "stack_height = nan", "global_fallback.stack_height"),
        ("stack_height = 3.0", "stack_height = 500.0", "outside stack.ranges"),
        ("exit_temperature = 295.4\n", "", "global_fallback.exit_temperature"),
        ("stack_height = [0.1, 450.0]", "stack_height = [450.0, 0.1]", "below maximum"),
        ("stack_height = [0.1, 450.0]", "stack_height = [0.1]", "[minimum, maximum]"),
        ('exit_velocity = "m/s"', 'exit_velocity = ""', "target_units.exit_velocity"),
        ("stack_height = 3.0", "stack_heigth = 3.0", "unknown quantities: stack_heigth"),
    ],
)
def test_invalid_rest(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message.replace("[", r"\[").replace("]", r"\]")):
        _load(tmp_path, PSTK + NEI + REST.replace(old, new, 1))


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('path = "fixtures/pstk.csv"', 'path = ""', "stack.pstk.path"),
        ('scc_column = "code"', "", "stack.pstk.scc_column"),
        ('fips_column = "region"', 'fips_column = " "', "stack.pstk.fips_column"),
        ('national_fips = ["0"]', "national_fips = [0]", "national_fips"),
        ('stack_height = "h"', "", "columns.stack_height"),
        ('exit_temperature = "degF"', "", "units.exit_temperature"),
    ],
)
def test_invalid_pstk(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, PSTK.replace(old, new, 1) + NEI + REST)


def test_missing_section(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="stack section is missing"):
        _load(tmp_path, "[other]\nx = 1\n")


def test_nei_explicit_values(tmp_path: Path) -> None:
    nei = _load(tmp_path, PSTK + NEI + REST).nei
    assert nei.directory == PROJECT_ROOT / "fixtures/nei"
    assert nei.shard_path("12") == PROJECT_ROOT / "fixtures/nei/n_12.csv.gz"
    assert (nei.prefix_digits, nei.id_column) == (2, "eis")
    assert (nei.max_candidates, nei.merge_significant_digits) == (3, 4)
    assert nei.columns["stack_height"] == "h"
    assert nei.units["exit_temperature"] == "degF"
    assert nei.raw_path == PROJECT_ROOT / "fixtures/raw.zip"
    assert (nei.raw_id_column, nei.raw_columns["exit_velocity"]) == ("FAC", "V")


def test_nei_default_file() -> None:
    nei = load_stack_settings().nei
    assert "{prefix}" in nei.file_template
    assert set(nei.columns) == set(STACK_QUANTITIES) == set(nei.raw_columns)
    assert nei.units == {
        "stack_height": "ft",
        "stack_diameter": "ft",
        "exit_velocity": "ft/s",
        "exit_temperature": "degF",
    }
    assert nei.max_candidates >= 1


def test_nei_tables_are_read_only(tmp_path: Path) -> None:
    nei = _load(tmp_path, PSTK + NEI + REST).nei
    with pytest.raises(TypeError):
        nei.units["stack_height"] = "m"  # type: ignore[index]


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('directory = "fixtures/nei"', 'directory = ""', "stack.nei.directory"),
        ('file_template = "n_{prefix}.csv.gz"', 'file_template = "n.csv.gz"', "{prefix}"),
        ("prefix_digits = 2", "prefix_digits = 0", "stack.nei.prefix_digits"),
        ("prefix_digits = 2", "prefix_digits = 1.5", "stack.nei.prefix_digits"),
        ("prefix_digits = 2", "prefix_digits = true", "stack.nei.prefix_digits"),
        ('id_column = "eis"', "", "stack.nei.id_column"),
        ("max_candidates = 3", "max_candidates = 0", "stack.nei.max_candidates"),
        ("max_candidates = 3", "max_candidates = -1", "stack.nei.max_candidates"),
        (
            "merge_significant_digits = 4",
            "merge_significant_digits = 0",
            "merge_significant_digits",
        ),
        ("merge_significant_digits = 4", "merge_significant_digits = 16", "1 to 15"),
        ("merge_significant_digits = 4", "merge_significant_digits = 2.5", "1 to 15"),
        ('raw_path = "fixtures/raw.zip"', "", "stack.nei.raw_path"),
        ('raw_id_column = "FAC"', "", "stack.nei.raw_id_column"),
        ('stack_height = "h"', "", "stack.nei.columns.stack_height"),
        ('exit_temperature = "degF"', "", "stack.nei.units.exit_temperature"),
        ('exit_velocity = "V"', "", "stack.nei.raw_columns.exit_velocity"),
    ],
)
def test_invalid_nei(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message.replace("{", r"\{").replace("}", r"\}")):
        _load(tmp_path, PSTK + NEI.replace(old, new, 1) + REST)


def test_nei_table_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="stack.nei"):
        _load(tmp_path, PSTK + REST)
