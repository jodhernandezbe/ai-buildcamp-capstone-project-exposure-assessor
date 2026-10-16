"""Smoke-test setup: load ``.env`` and skip CompTox tests when the CompTox key is missing."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from config.loader import get_comptox_settings


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    load_dotenv()
    variable = get_comptox_settings().api_key_env_var
    if os.environ.get(variable, "").strip():
        return
    skip = pytest.mark.skip(reason=f"{variable} is not set")
    for item in items:
        if "comptox" in item.keywords:
            item.add_marker(skip)
