"""The result of one PubChem step: a value, or the reason there is none."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lookup[T]:
    """A value read from PubChem, or why it could not be.

    Attributes:
        value: The value, or None if it could not be obtained.
        reason: Why ``value`` is None; None when there is a value.
    """

    value: T | None
    reason: str | None = None

    @classmethod
    def found(cls, value: T) -> Lookup[T]:
        """A successful step."""
        return cls(value, None)

    @classmethod
    def missing(cls, reason: str) -> Lookup[T]:
        """A failed step with its reason."""
        return cls(None, reason)
