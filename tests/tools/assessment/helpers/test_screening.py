"""Tests for the arithmetic of the tiered screen (synthetic, linear fake exposure)."""

from __future__ import annotations

import pytest

from tests.tools.assessment.factories import SCREENING, TOXICITY, FakeSteps, hq_of, stack
from tools.assessment.helpers.screening import (
    can_screen,
    exceedance,
    reaches,
    scaled,
    unit_bound,
    worst_case,
)
from tools.schemas import Toxicity

TEMPERATURES = SCREENING.ambient_temperatures_k  # 250 K and 300 K


def test_the_unit_bound_is_the_generic_stack_at_1_g_s_on_the_worst_temperature() -> None:
    fake = FakeSteps()
    unit = unit_bound(fake.steps(), TOXICITY, TEMPERATURES)
    assert unit.hq == pytest.approx(hq_of(1.0, 3.0, 300.0))  # the hotter day gives more
    assert unit.cancer_risk is None  # no IUR
    assert ("pstk", None) in fake.calls
    assert not any(name in {"weather", "people"} for name, _ in fake.calls)


def test_the_worst_case_takes_the_highest_stack_and_drops_the_representative_case() -> None:
    worst = worst_case(2.0, [stack(10), stack(4)], TOXICITY, FakeSteps().steps(), TEMPERATURES)
    assert worst.hq == pytest.approx(hq_of(2.0, 4.0, 300.0))
    ranges = worst.exposure["range"]
    assert ranges is not None and ranges["representative"] == {
        "max_concentration": None,
        "hq": None,
        "cancer_risk": None,
    }
    assert all(r["representative"]["hq"] is None for r in worst.exposure["results"])


def test_bounds_scale_with_the_emission_rate() -> None:
    unit = unit_bound(FakeSteps().steps(), Toxicity(rfc=1.0, iur=1.0), TEMPERATURES)
    bound = scaled(unit, 3.0)
    assert bound["hq"] == pytest.approx(3.0 * (unit.hq or 0))
    assert bound["cancer_risk"] == pytest.approx(3.0 * (unit.cancer_risk or 0))


def test_without_any_benchmark_nothing_can_be_screened() -> None:
    unit = unit_bound(FakeSteps().steps(), Toxicity(rfc=None, iur=None), TEMPERATURES)
    assert not can_screen(unit) and scaled(unit, 5.0) == {"hq": None, "cancer_risk": None}


@pytest.mark.parametrize(
    ("hq", "risk", "expected"),
    [
        (0.1, None, True),  # at the threshold counts
        (0.09, None, False),
        (0.01, 2e-6, True),  # the cancer risk alone is enough
        (None, 5e-7, False),
        (None, None, False),  # nothing known is not a reason to go on (the caller decides)
    ],
)
def test_thresholds(hq: float | None, risk: float | None, expected: bool) -> None:
    assert reaches(hq, risk, SCREENING) is expected


def test_exceedance_is_the_larger_ratio_to_its_threshold() -> None:
    assert exceedance(0.2, 5e-6, SCREENING) == pytest.approx(5.0)
    assert exceedance(None, None, SCREENING) == -1.0
