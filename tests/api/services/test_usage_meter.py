"""Tests for token accounting and cost estimation."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult

from api.services.usage_meter import CallUsage, UsageRecorder, estimate_cost, summarize
from config.ui import ModelPrice

PRICE = ModelPrice(
    input_usd_per_mtok=2.0,
    cached_input_usd_per_mtok=0.5,
    output_usd_per_mtok=8.0,
    priced_on=date(2026, 1, 2),
    source_url="https://example.test/pricing",
)
PRICING = {"m": PRICE}


def _result(*messages: AIMessage) -> LLMResult:
    return LLMResult(generations=[[ChatGeneration(message=m) for m in messages]])


def _with_usage(input_tokens: int, output_tokens: int, cached: int = 0) -> AIMessage:
    usage = UsageMetadata(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        input_token_details={"cache_read": cached},
    )
    return AIMessage(content="x", usage_metadata=usage)


def test_recorder_counts_every_call_with_its_reported_usage() -> None:
    recorder = UsageRecorder("m")
    recorder.on_llm_end(_result(_with_usage(100, 20, cached=40)), run_id=uuid4())
    recorder.on_llm_end(_result(_with_usage(10, 5)), run_id=uuid4())
    assert recorder.calls == [CallUsage("m", 100, 40, 20), CallUsage("m", 10, 0, 5)]


def test_a_call_without_usage_is_unknown_not_zero() -> None:
    recorder = UsageRecorder("m")
    recorder.on_llm_end(_result(AIMessage(content="x")), run_id=uuid4())
    assert recorder.calls == [CallUsage("m", None, 0, None)]
    assert recorder.calls[0].known is False


def test_cost_bills_cached_tokens_at_the_cached_price() -> None:
    # 60 uncached x 2.0 + 40 cached x 0.5 + 20 output x 8.0, per million tokens
    cost = estimate_cost([CallUsage("m", 100, 40, 20)], PRICING)
    assert cost.usd == pytest.approx((60 * 2.0 + 40 * 0.5 + 20 * 8.0) / 1_000_000)
    assert (cost.status, cost.priced_on) == ("estimate", "2026-01-02")


def test_an_unpriced_model_has_tokens_but_no_cost() -> None:
    cost = estimate_cost([CallUsage("other", 100, 0, 20)], PRICING)
    assert (cost.usd, cost.status, cost.priced_on) == (None, "unpriced", None)


def test_incomplete_usage_makes_the_cost_a_lower_bound() -> None:
    calls = [CallUsage("m", 1000, 0, 100), CallUsage("m", None, 0, None)]
    cost = estimate_cost(calls, PRICING)
    assert cost.status == "lower_bound"
    assert cost.usd == pytest.approx((1000 * 2.0 + 100 * 8.0) / 1_000_000)


def test_no_calls_cost_nothing() -> None:
    cost = estimate_cost([], PRICING)
    assert (cost.usd, cost.status) == (0.0, "estimate")


def test_cached_tokens_never_exceed_input_in_the_bill() -> None:
    cost = estimate_cost([CallUsage("m", 10, 50, 0)], PRICING)  # a provider reporting nonsense
    assert cost.usd == pytest.approx(10 * 0.5 / 1_000_000)


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
