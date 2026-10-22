"""Scenario ``full-assessment-with-nei-stacks``: a CAS whose facilities have their own stacks.

The agent must fetch the chemical and assess every one of its TRI facilities, by the batch
assessment or by hand (then: NEI stacks, weather and population per facility, the exposure
calculation once with every NEI candidate, no industry/SCC fallback), name each facility in
the report, and write the full report (checked by an LLM judge). Network
tools replay the live outputs recorded in ``evals/cassettes/`` (record them with
``uv run python -m evals record full-assessment-with-nei-stacks``).

Run with: ``uv run pytest -m eval tests/evals/test_full_assessment.py``
"""

from __future__ import annotations

import pytest

from evals.record import RunRecord
from evals.scenarios import FULL_ASSESSMENT
from evals.scoring import ScenarioScore
from evals.suite import cassette_path, evaluate

pytestmark = pytest.mark.eval


@pytest.fixture(scope="module")
def scored() -> tuple[RunRecord, ScenarioScore]:
    if not cassette_path(FULL_ASSESSMENT).is_file():
        pytest.skip(f"no cassette; run: uv run python -m evals record {FULL_ASSESSMENT.id}")
    return evaluate(FULL_ASSESSMENT)


@pytest.mark.parametrize("check", [c.name for c in FULL_ASSESSMENT.checks])
def test_check(scored: tuple[RunRecord, ScenarioScore], check: str) -> None:
    _, score = scored
    (outcome,) = [o for o in score.outcomes if o.name == check]
    assert outcome.passed, f"{check}: {outcome.reason}\n\nreport: {score.report_path}"


def test_llm_judge_complete_report(scored: tuple[RunRecord, ScenarioScore]) -> None:
    record, score = scored
    failed = [f for f in score.failures() if f.startswith("judge: ")]
    assert not failed, f"{record.report}\n\n" + "\n".join(failed)
