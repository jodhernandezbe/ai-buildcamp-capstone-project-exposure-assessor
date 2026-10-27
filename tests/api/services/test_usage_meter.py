"""Tests for the usage totals shaped for the wire contract."""

from __future__ import annotations

from datetime import date

from api.services.usage_meter import summarize
from app.usage_meter import CallUsage
from config.ui import ModelPrice

PRICE = ModelPrice(
    input_usd_per_mtok=2.0,
    cached_input_usd_per_mtok=0.5,
    output_usd_per_mtok=8.0,
    priced_on=date(2026, 1, 2),
    source_url="https://example.test/pricing",
)
PRICING = {"m": PRICE}


def test_summary_totals_and_completeness() -> None:
    calls = [CallUsage("m", 100, 40, 20), CallUsage("m", 10, 0, 5), CallUsage("m", None, 0, None)]
    totals = summarize(calls, PRICING)
    assert (totals.calls, totals.input_tokens, totals.cached_input_tokens) == (3, 110, 40)
    assert (totals.output_tokens, totals.complete) == (25, False)
    assert totals.cost_status == "lower_bound"


def test_summary_of_unpriced_model_keeps_tokens() -> None:
    totals = summarize([CallUsage("other", 100, 0, 20)], PRICING)
    assert (totals.input_tokens, totals.output_tokens) == (100, 20)
    assert (totals.cost_usd, totals.cost_status) == (None, "unpriced")
