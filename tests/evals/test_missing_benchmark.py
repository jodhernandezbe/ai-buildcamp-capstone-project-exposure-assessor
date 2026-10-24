"""Scenario ``missing-benchmark-asks``: a needed inhalation unit risk is missing.

Acrolein has an RfC in CompTox but no unit risk, so a cancer risk cannot be concluded. The agent
must stop after looking the chemical up, say which value is missing and why, and offer the user
both answers (enter it, or proceed without it). It must not run the exposure calculation.

Run with: ``uv run pytest -m eval tests/evals/test_missing_benchmark.py``
"""

from __future__ import annotations

import pytest

from evals.record import RunRecord
from evals.scenarios import MISSING_BENCHMARK
from evals.scoring import ScenarioScore
from evals.suite import evaluate

pytestmark = pytest.mark.eval


@pytest.fixture(scope="module")
def scored() -> tuple[RunRecord, ScenarioScore]:
    return evaluate(MISSING_BENCHMARK)


@pytest.fixture(scope="module")
def record(scored: tuple[RunRecord, ScenarioScore]) -> RunRecord:
    return scored[0]


def test_run_completes(record: RunRecord) -> None:
    assert record.completed, f"run did not finish: {record.error}"


def test_the_chemical_is_looked_up_by_its_cas_number(record: RunRecord) -> None:
    names = [c.name for c in record.calls]
    assert "fetch_chemical_properties" in names, f"no lookup: {names}"


def test_no_exposure_is_computed_without_the_unit_risk(record: RunRecord) -> None:
    called = [c.name for c in record.calls if c.name == "calculate_exposure_metrics"]
    assert not called, "the agent computed an exposure before the missing value was supplied"


def test_reply_names_the_missing_value_and_both_answers(
    scored: tuple[RunRecord, ScenarioScore],
) -> None:
    record, score = scored
    text = record.report.lower()
    assert "iur" in text, f"reply does not name the missing unit risk:\n{record.report}"
    assert "proceed without" in text, f"reply does not offer to proceed:\n{record.report}"
    failed = [f for f in score.failures() if f.startswith("judge: ")]
    assert not failed, f"LLM judge failed:\n{record.report}\n" + "\n".join(failed)
