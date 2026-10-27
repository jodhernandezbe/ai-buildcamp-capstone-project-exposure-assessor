"""Token accounting and estimated cost for chat model calls.

Usage comes only from what the provider reports; a call that reports none is counted as
unknown, never as zero. Cost comes only from the prices in configuration. Shared by the
command line and the web server, so both meter a run the same way.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult

from config.ui import ModelPrice

_PER_MILLION = 1_000_000


@dataclass(frozen=True)
class CallUsage:
    """Usage of one chat model call; ``None`` tokens mean the provider reported no usage.

    Attributes:
        model: Configured model name (the key into the price table).
        input_tokens: All input tokens, cached ones included.
        cached_input_tokens: Input tokens served from the provider's cache.
        output_tokens: Output tokens.
    """

    model: str
    input_tokens: int | None
    cached_input_tokens: int
    output_tokens: int | None

    @property
    def known(self) -> bool:
        """True when the provider reported this call's usage."""
        return self.input_tokens is not None and self.output_tokens is not None


class UsageRecorder(BaseCallbackHandler):
    """Collects the usage of every chat model call of a run (all of them, the agent's and the
    scope classifier's, as long as this handler is in the run configuration)."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.calls: list[CallUsage] = []

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: object,
    ) -> None:
        """Record one entry per generation of the finished call."""
        for generation in (g for batch in response.generations for g in batch):
            message = generation.message if isinstance(generation, ChatGeneration) else None
            usage = message.usage_metadata if isinstance(message, AIMessage) else None
            self.calls.append(self._call(usage))

    def _call(self, usage: UsageMetadata | None) -> CallUsage:
        if not usage:
            return CallUsage(self.model, None, 0, None)
        details = usage.get("input_token_details")
        return CallUsage(
            model=self.model,
            input_tokens=usage["input_tokens"],
            cached_input_tokens=details.get("cache_read", 0) if details else 0,
            output_tokens=usage["output_tokens"],
        )


@dataclass(frozen=True)
class Cost:
    """Estimated cost in USD, or why there is none.

    ``status`` is ``estimate`` (every call priced and reported), ``lower_bound`` (some call
    reported no usage) or ``unpriced`` (a model has no configured price; ``usd`` is None).
    """

    usd: float | None
    status: str
    priced_on: str | None


def _call_cost(call: CallUsage, price: ModelPrice) -> float:
    cached = min(call.cached_input_tokens, call.input_tokens or 0)
    uncached = (call.input_tokens or 0) - cached
    return (
        uncached * price.input_usd_per_mtok
        + cached * price.cached_input_usd_per_mtok
        + (call.output_tokens or 0) * price.output_usd_per_mtok
    ) / _PER_MILLION


def estimate_cost(calls: Sequence[CallUsage], pricing: Mapping[str, ModelPrice]) -> Cost:
    """Price ``calls`` from ``pricing``; never guesses a price or a missing call's usage."""
    prices = [pricing.get(call.model) for call in calls]
    if any(price is None for price in prices):
        return Cost(usd=None, status="unpriced", priced_on=None)
    known = [
        (call, price) for call, price in zip(calls, prices, strict=True) if price and call.known
    ]
    total = sum(_call_cost(call, price) for call, price in known)
    dates = [price.priced_on.isoformat() for _, price in known]
    complete = len(known) == len(calls)
    return Cost(
        usd=total,
        status="estimate" if complete else "lower_bound",
        priced_on=max(dates) if dates else None,
    )


@dataclass(frozen=True)
class UsageSummary:
    """Totals of a set of calls: the tokens of the calls that reported usage, whether all did,
    and the cost.

    Attributes:
        calls: Number of calls, including those that reported no usage.
        input_tokens: Input tokens of the calls with known usage (cached ones included).
        cached_input_tokens: Input tokens served from the provider's cache.
        output_tokens: Output tokens.
        complete: True when every call reported its usage.
        cost: Estimated cost of the calls.
    """

    calls: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    complete: bool
    cost: Cost


def summarize_calls(calls: Sequence[CallUsage], pricing: Mapping[str, ModelPrice]) -> UsageSummary:
    """Total ``calls``; a call that reported no usage adds no tokens and marks the total
    incomplete."""
    known = [call for call in calls if call.known]
    return UsageSummary(
        calls=len(calls),
        input_tokens=sum(call.input_tokens or 0 for call in known),
        cached_input_tokens=sum(call.cached_input_tokens for call in known),
        output_tokens=sum(call.output_tokens or 0 for call in known),
        complete=len(known) == len(calls),
        cost=estimate_cost(calls, pricing),
    )


def format_usage(total: UsageSummary) -> str:
    """The run's usage and estimated cost as two lines of text (the command line's summary).

    The cost is always called an estimate, and says when it is only a lower bound or when the
    model has no configured price; a figure is never printed for what could not be priced.
    """
    tokens = (
        f"Usage: {total.calls} model calls, {total.input_tokens:,} input tokens "
        f"({total.cached_input_tokens:,} cached), {total.output_tokens:,} output tokens"
    )
    return f"{tokens}\n{_cost_line(total.cost)}"


def _cost_line(cost: Cost) -> str:
    if cost.usd is None:
        return "Estimated cost: unpriced (no price is configured for the model)"
    priced = f"prices of {cost.priced_on}" if cost.priced_on else "no prices used"
    if cost.status == "lower_bound":
        return f"Estimated cost: at least ${cost.usd:.4f}; some calls reported no usage ({priced})"
    return f"Estimated cost: ${cost.usd:.4f} ({priced})"
