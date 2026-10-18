"""Live smoke test for fetch_stack_parameters_from_nei against EPA Envirofacts.

Run with ``uv run pytest -m smoke`` (needs network access; no API key). The FRS lookup is live;
the stack table is the committed one. The checks are on shape and plausibility, not on values.
"""

from __future__ import annotations

import httpx
import pytest

from config.efservice import get_efservice_settings, get_frs_settings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.stack.frs import eis_ids_for_frs
from tools.emissions.stack import fetch_stack_parameters_from_nei

pytestmark = pytest.mark.smoke

# A facility known to be registered in the EIS program (the example in the design notes).
REGISTERED_FRS_ID = "110021074834"


def test_frs_id_resolves_to_an_eis_id() -> None:
    with httpx.Client() as http:
        client = EfserviceClient(get_efservice_settings(), http)
        result = eis_ids_for_frs(REGISTERED_FRS_ID, client, get_frs_settings())
    assert result.eis_ids
    assert all(eis_id.isdigit() for eis_id in result.eis_ids)


def test_unknown_frs_id_gives_a_warning_not_an_error() -> None:
    result = fetch_stack_parameters_from_nei.invoke({"frs_id": "110000000000"})
    assert result["candidates"] == []
    assert result["warnings"]


def test_candidates_when_present_are_plausible_and_ordered() -> None:
    result = fetch_stack_parameters_from_nei.invoke({"frs_id": REGISTERED_FRS_ID})
    heights = [c["stack_height"] for c in result["candidates"]]
    assert heights == sorted(h for h in heights if h is not None)
    for candidate in result["candidates"]:
        assert candidate["source"] == "NEI"
        assert candidate["exit_temperature"] is not None
        assert 200 <= candidate["exit_temperature"] <= 1800
