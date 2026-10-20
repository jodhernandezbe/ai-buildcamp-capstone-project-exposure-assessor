"""Scenario ``chemical-name-only``: the user names a chemical but gives no CAS number.

No tool turns a name into a CAS number, so the agent must ask for it instead of filling one
in from memory (for formaldehyde the model knows "50-00-0"). The agent runs with the chat model
configured in ``[agent]`` (the same one the program runs, built by ``app.chat_model``) and the
production prompt and tool descriptions; every network tool is replayed from an
empty cassette, so any call fails closed and is visible in the record.

Run with: ``uv run pytest -m eval tests/evals/test_chemical_name_only.py``
"""

from __future__ import annotations

import re

import pytest

from evals.record import RunRecord
from evals.scenarios import CHEMICAL_NAME_ONLY
from evals.scoring import ScenarioScore
from evals.suite import evaluate

pytestmark = pytest.mark.eval

CAS_PATTERN = re.compile(r"\b\d{2,7}-\d{2}-\d\b")


@pytest.fixture(scope="module")
def scored() -> tuple[RunRecord, ScenarioScore]:
    return evaluate(CHEMICAL_NAME_ONLY)


@pytest.fixture(scope="module")
def record(scored: tuple[RunRecord, ScenarioScore]) -> RunRecord:
    return scored[0]


def test_run_completes(record: RunRecord) -> None:
    assert record.completed, f"run did not finish: {record.error}"


def test_no_tool_is_called(record: RunRecord) -> None:
    called = [f"{c.name}({c.args})" for c in record.calls]
    assert not called, f"agent called tools instead of asking for the CAS number: {called}"


def test_no_cas_number_is_invented(record: RunRecord) -> None:
    assert not CAS_PATTERN.search(record.report), f"report states a CAS number:\n{record.report}"


def test_llm_judge_reply_asks_for_cas(scored: tuple[RunRecord, ScenarioScore]) -> None:
    record, score = scored
    failed = [f for f in score.failures() if f.startswith("judge: ")]
    assert not failed, (
        f"LLM judge failed the reply:\n{record.report}\n\n"
        + "\n".join(failed)
        + f"\n\nreport: {score.report_path}"
    )
