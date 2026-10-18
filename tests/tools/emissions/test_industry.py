"""Tests for fetch_facility_industry (no network: a mock Envirofacts)."""

from __future__ import annotations

import httpx
import pytest

from tools.emissions import industry
from tools.emissions.industry import fetch_facility_industry

DOC = "1313000000001"


@pytest.fixture
def requests_seen(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "REF_NAICS" in request.url.path:
            return httpx.Response(
                200, json=[{"naics_code": "324110", "naics_desc": "Petroleum Refineries"}]
            )
        row = {
            "naics_code": "324110",
            "primary_ind": "1",
            "naics_sequence_num": 1,
            "source": "Reported",
        }
        return httpx.Response(200, json=[row])

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(industry, "_open_client", lambda: httpx.Client(transport=transport))
    return seen


def test_schema() -> None:
    assert fetch_facility_industry.name == "fetch_facility_industry"
    assert set(fetch_facility_industry.args) == {"doc_ctrl_num"}


def test_returns_the_title_in_words(requests_seen: list[httpx.Request]) -> None:
    result = fetch_facility_industry.invoke({"doc_ctrl_num": DOC})
    assert result["naics_code"] == "324110"
    assert result["naics_title"] == "Petroleum Refineries"
    assert result["code_origin"] == "reported"
    assert result["source"] == "TRI submission NAICS"
    assert result["warnings"] == []
    assert len(requests_seen) == 2


def test_accepts_a_number(requests_seen: list[httpx.Request]) -> None:
    assert (
        fetch_facility_industry.invoke({"doc_ctrl_num": 1313000000001})["naics_title"]
        == "Petroleum Refineries"
    )


def test_an_invalid_number_returns_nulls_without_a_request(
    requests_seen: list[httpx.Request],
) -> None:
    result = fetch_facility_industry.invoke({"doc_ctrl_num": "abc"})
    assert result["naics_code"] is None and result["naics_title"] is None
    assert result["warnings"] and requests_seen == []


def test_description_says_what_to_do_with_the_result() -> None:
    text = " ".join(fetch_facility_industry.description.split())
    for phrase in ("`naics_title`", "SCC process search", "`doc_ctrl_num`", "null", "do not guess"):
        assert phrase in text, phrase
