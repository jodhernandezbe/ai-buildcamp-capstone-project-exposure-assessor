"""Smoke-test setup: load ``.env`` and skip tests whose API key is missing.

A test marked ``comptox`` needs the CompTox key, one marked ``census`` the Census key and one
marked ``logfire`` the Logfire read token; the
environment variable names come from the settings, never from here.
"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from config.loader import get_comptox_settings
from config.population import get_population_settings
from config.telemetry import get_telemetry_settings


def _key_variables() -> dict[str, str]:
    """Marker name -> the environment variable holding that service's API key."""
    return {
        "comptox": get_comptox_settings().api_key_env_var,
        "census": get_population_settings().api_key_env_var,
        "logfire": get_telemetry_settings().read_token_env_var,
    }


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    load_dotenv()
    for marker, variable in _key_variables().items():
        if os.environ.get(variable, "").strip():
            continue
        skip = pytest.mark.skip(reason=f"{variable} is not set")
        for item in items:
            if marker in item.keywords:
                item.add_marker(skip)
