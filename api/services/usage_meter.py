"""Turn and session usage totals for the wire contract.

The accounting itself (call recording, cost estimation) is ``app.usage_meter``; this module
only shapes its result for the web contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from api.schemas.chat import UsageTotals
from app.usage_meter import CallUsage, summarize_calls
from config.ui import ModelPrice


def summarize(calls: Sequence[CallUsage], pricing: Mapping[str, ModelPrice]) -> UsageTotals:
    """Totals of ``calls`` for the contract: tokens of the calls that reported usage, whether
    all did, and the cost."""
    total = summarize_calls(calls, pricing)
    return UsageTotals(
        calls=total.calls,
        input_tokens=total.input_tokens,
        cached_input_tokens=total.cached_input_tokens,
        output_tokens=total.output_tokens,
        complete=total.complete,
        cost_usd=total.cost.usd,
        cost_status=total.cost.status,  # pyright: ignore[reportArgumentType]
        priced_on=total.cost.priced_on,
    )
