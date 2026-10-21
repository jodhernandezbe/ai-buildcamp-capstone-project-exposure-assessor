"""Token accounting and estimated cost for chat model calls.

Usage comes only from what the provider reports; a call that reports none is counted as
unknown, never as zero. Cost comes only from the prices in configuration.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, UsageMetadata
from langchain_core.outputs import ChatGeneration, LLMResult

from api.schemas.chat import UsageTotals
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


def summarize(calls: Sequence[CallUsage], pricing: Mapping[str, ModelPrice]) -> UsageTotals:
    """Totals of ``calls`` for the contract: tokens of the calls that reported usage, whether
    all did, and the cost."""
    known = [call for call in calls if call.known]
    cost = estimate_cost(calls, pricing)
    return UsageTotals(
        calls=len(calls),
        input_tokens=sum(call.input_tokens or 0 for call in known),
        cached_input_tokens=sum(call.cached_input_tokens for call in known),
        output_tokens=sum(call.output_tokens or 0 for call in known),
        complete=len(known) == len(calls),
        cost_usd=cost.usd,
        cost_status=cost.status,  # pyright: ignore[reportArgumentType]
        priced_on=cost.priced_on,
    )
