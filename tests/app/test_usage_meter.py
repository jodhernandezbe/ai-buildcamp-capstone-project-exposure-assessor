"""Tests for token accounting and cost estimation."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult

from app.usage_meter import (
    CallUsage,
    UsageRecorder,
    estimate_cost,
    format_usage,
    summarize_calls,
)
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
    total = summarize_calls(calls, PRICING)
    assert (total.calls, total.input_tokens, total.cached_input_tokens) == (3, 110, 40)
    assert (total.output_tokens, total.complete, total.cost.status) == (25, False, "lower_bound")


def test_summary_of_no_calls_is_complete_and_free() -> None:
    total = summarize_calls([], PRICING)
    assert (total.calls, total.complete, total.cost.usd) == (0, True, 0.0)


def test_the_summary_labels_the_cost_an_estimate_with_its_price_date() -> None:
    text = format_usage(summarize_calls([CallUsage("m", 1200, 200, 300)], PRICING))
    assert text.splitlines()[0] == (
        "Usage: 1 model calls, 1,200 input tokens (200 cached), 300 output tokens"
    )
    assert text.splitlines()[1].startswith("Estimated cost: $0.")
    assert "prices of 2026-01-02" in text


def test_the_summary_of_incomplete_usage_is_a_lower_bound() -> None:
    calls = [CallUsage("m", 1000, 0, 100), CallUsage("m", None, 0, None)]
    line = format_usage(summarize_calls(calls, PRICING)).splitlines()[1]
    assert line.startswith("Estimated cost: at least $")
    assert "reported no usage" in line


def test_the_summary_of_an_unpriced_model_prints_tokens_and_no_amount() -> None:
    text = format_usage(summarize_calls([CallUsage("other", 100, 0, 20)], PRICING))
    assert "100 input tokens" in text
    assert text.splitlines()[1] == "Estimated cost: unpriced (no price is configured for the model)"
    assert "$" not in text
