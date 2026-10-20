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

from app.chat_model import build_chat_model
from config.agent import get_agent_settings
from config.evaluation import get_evaluation_settings
from evals.cassette import Cassette, replay_tools
from evals.record import RunRecord
from evals.runner import run_scenario
from evals.scenarios import CHEMICAL_NAME_ONLY
from evals.scoring import judge_records
from tools.registry import get_all_tools

pytestmark = pytest.mark.eval

CAS_PATTERN = re.compile(r"\b\d{2,7}-\d{2}-\d\b")


@pytest.fixture(scope="module")
def record() -> RunRecord:
    settings = get_evaluation_settings()
    cassette = Cassette.load(settings.cassette_dir / f"{CHEMICAL_NAME_ONLY.id}.json")
    tools = replay_tools(get_all_tools(), cassette, settings.live_tools)
    agent_settings = get_agent_settings()
    model = build_chat_model(agent_settings)
    scenario = (CHEMICAL_NAME_ONLY.id, CHEMICAL_NAME_ONLY.query)
    return run_scenario(model, tools, scenario, agent_settings)


def test_run_completes(record: RunRecord) -> None:
    assert record.completed, f"run did not finish: {record.error}"


def test_no_tool_is_called(record: RunRecord) -> None:
    called = [f"{c.name}({c.args})" for c in record.calls]
    assert not called, f"agent called tools instead of asking for the CAS number: {called}"


def test_no_cas_number_is_invented(record: RunRecord) -> None:
    assert not CAS_PATTERN.search(record.report), f"report states a CAS number:\n{record.report}"


def test_llm_judge_reply_asks_for_cas(record: RunRecord) -> None:
    (verdicts,) = judge_records([record], CHEMICAL_NAME_ONLY.judges, get_evaluation_settings())
    failed = [f"{v.judge}: {v.reasoning}" for v in verdicts if not v.passed]
    assert not failed, f"LLM judge failed the reply:\n{record.report}\n\n" + "\n".join(failed)
