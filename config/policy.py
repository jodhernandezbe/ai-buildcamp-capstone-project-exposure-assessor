"""The request policy shared by the settings of every polled outside service."""

from __future__ import annotations

from dataclasses import dataclass

from config.parsing import require_int, require_number


@dataclass(frozen=True)
class RequestPolicy:
    """How politely a service is called.

    Attributes:
        delay_seconds: Wait before each request, in seconds.
        timeout_seconds: Per-request timeout, in seconds.
        max_retries: Retries after a throttled, failed or timed-out request.
        backoff_seconds: First retry wait in seconds; doubles on each further retry.
    """

    delay_seconds: float
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float


def parse_policy(table: dict[str, object], name: str) -> RequestPolicy:
    """Read the four policy values from ``table``; raises ``ValueError`` naming a bad key."""
    return RequestPolicy(
        delay_seconds=require_number(table, "delay_seconds", minimum=0, name=name),
        timeout_seconds=require_number(table, "timeout_seconds", minimum=0.001, name=name),
        max_retries=require_int(table, "max_retries", minimum=0, name=name),
        backoff_seconds=require_number(table, "backoff_seconds", minimum=0, name=name),
    )
