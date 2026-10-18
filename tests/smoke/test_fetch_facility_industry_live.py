"""Live smoke test for fetch_facility_industry against EPA Envirofacts (no key needed).

Run with ``uv run pytest -m smoke``. The control numbers are two real TRI submissions of one
facility whose NAICS code is known: 1988 (EPA-assigned) and 2013 (reported by the facility).
"""

from __future__ import annotations

import pytest

from tools.emissions.industry import fetch_facility_industry

pytestmark = pytest.mark.smoke

ASSIGNED_1988 = "1388025696232"
REPORTED_2013 = "1313211440122"


def test_a_reported_code_has_a_title_in_words() -> None:
    result = fetch_facility_industry.invoke({"doc_ctrl_num": REPORTED_2013})
    assert result["naics_code"] == "313310"
    assert result["naics_title"] == "Textile and Fabric Finishing Mills"
    assert result["code_origin"] == "reported"
    assert result["warnings"] == []


def test_an_assigned_code_is_flagged() -> None:
    result = fetch_facility_industry.invoke({"doc_ctrl_num": ASSIGNED_1988})
    assert result["naics_code"] == "335999"
    assert result["naics_title"] and not result["naics_title"].isdigit()
    assert result["code_origin"] == "assigned"
    assert any("EPA assigned" in w for w in result["warnings"])


def test_an_unknown_submission_is_a_warning_not_an_error() -> None:
    result = fetch_facility_industry.invoke({"doc_ctrl_num": "9999999999999"})
    assert result["naics_code"] is None and result["naics_title"] is None
    assert result["warnings"]
