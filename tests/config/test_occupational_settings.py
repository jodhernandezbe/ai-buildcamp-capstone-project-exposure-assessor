"""Tests for the ``[occupational]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.occupational import load_occupational_settings

TEXT = """
[occupational]
shift_inhalation_m3 = 10.0
daily_inhalation_m3 = 20.0
worker_days_per_year = 250.0
tenure_years = 40.0
lifetime_years = 78.0
twa_hours = 8.0
low_volatility_mmhg = 0.001

[occupational.thresholds]
exceedance_ratio = 1.0
elevated_ratio = 0.1
exceedance_hq = 1.0
elevated_hq = 0.1
exceedance_cancer_risk = 1e-4
elevated_cancer_risk = 1e-6

[occupational.ventilation.baseline]
label = "Baseline"
rate_ft3_per_min = 3000.0
mixing_factor = 0.5

[occupational.ventilation.worst_case]
label = "Worst"
rate_ft3_per_min = 500.0
mixing_factor = 0.1
"""


def test_loads_values(tmp_path: Path) -> None:
    settings = load_occupational_settings(_write(tmp_path, TEXT))
    assert settings.baseline.rate_ft3_per_min == 3000.0
    assert settings.worst_case.mixing_factor == 0.1
    assert settings.thresholds.elevated_cancer_risk == 1e-6


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ("mixing_factor = 0.5", "mixing_factor = 1.5", "mixing_factor"),
        ("rate_ft3_per_min = 3000.0", "rate_ft3_per_min = 0", "rate_ft3_per_min"),
        ("worker_days_per_year = 250.0", "worker_days_per_year = 400", "worker_days_per_year"),
        ("tenure_years = 40.0", "tenure_years = 90.0", "tenure_years"),
        ("shift_inhalation_m3 = 10.0", "shift_inhalation_m3 = 30.0", "shift_inhalation_m3"),
        ("elevated_hq = 0.1", "elevated_hq = 2.0", "elevated_hq"),
        ("twa_hours = 8.0", "twa_hours = true", "twa_hours"),
    ],
)
def test_invalid_values_name_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    with pytest.raises(ValueError, match=key):
        load_occupational_settings(_write(tmp_path, TEXT.replace(old, new, 1)))


def test_default_file_loads() -> None:
    assert load_occupational_settings().lifetime_years == 78.0
