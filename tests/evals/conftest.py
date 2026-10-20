"""Evaluation setup: load ``.env`` and skip ``eval`` tests when a model API key is missing.

The agent's key variable comes from ``[agent]`` (the same model the program runs) and the
judge's from ``[evaluation]``.
"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from config.agent import get_agent_settings
from config.evaluation import get_evaluation_settings


def _missing_key() -> str | None:
    variables = (
        get_agent_settings().api_key_env_var,
        get_evaluation_settings().judge_api_key_env_var,
    )
    return next((v for v in variables if not os.environ.get(v, "").strip()), None)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    load_dotenv()
    variable = _missing_key()
    if variable is None:
        return
    skip = pytest.mark.skip(reason=f"{variable} is not set")
    for item in items:
        if "eval" in item.keywords:
            item.add_marker(skip)
