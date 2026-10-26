"""How the report prints a value: rounded for display only, or "not reported" with its reason.

Mirrors the interface's formatting (``frontend/src/lib/format.ts``) so the report and the
dashboard show the same text. Nothing here computes a quantity; it only writes one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import TypeIs

# Magnitudes outside [1e-3, 1e5) are written in scientific notation, like a cancer risk.
_SMALLEST_PLAIN = 1e-3
_LARGEST_PLAIN = 1e5
_REPORTED_DECIMALS = 6
_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


@dataclass(frozen=True)
class ValueFormat:
    """Display rules: significant digits and the text of an absent value."""

    digits: int
    not_reported: str

    def absent(self, reason: str | None = None) -> str:
        """``not reported``, followed by the reason when one is given."""
        return f"{self.not_reported} ({reason})" if reason else self.not_reported

    def number(self, value: float | None, unit: str = "", reason: str | None = None) -> str:
        """A metric with ``digits`` significant digits and its unit, or absent."""
        if not _finite(value):
            return self.absent(reason)
        text = _metric(float(value), self.digits)
        return f"{text} {unit}" if unit else text

    def reported(self, value: float | None, unit: str = "") -> str:
        """A quantity exactly as a source reported it (a release, hours), not rounded."""
        if not _finite(value):
            return self.absent()
        text = _plain(round(float(value), _REPORTED_DECIMALS))
        return f"{text} {unit}" if unit else text

    def count(self, value: int | None) -> str:
        """A whole count with thousands separators, or absent."""
        return self.absent() if value is None else f"{value:,}"

    def text(self, value: str | None) -> str:
        """Text a tool reported, or absent."""
        return value.strip() if value and value.strip() else self.absent()

    def flag(self, value: bool | None) -> str:
        """Yes / No, or absent."""
        return self.absent() if value is None else ("Yes" if value else "No")

    def span(self, low: float | None, high: float | None, unit: str = "") -> str:
        """One value when both ends print the same, else ``low – high``."""
        first, last = self.number(low), self.number(high)
        text = first if first == last else f"{first} – {last}"
        return f"{text} {unit}" if unit and _finite(low) and _finite(high) else text


def _finite(value: float | None) -> TypeIs[float]:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _plain(value: float) -> str:
    """The value without exponent or trailing zeros: 48200.0 -> "48200", 0.50 -> "0.5"."""
    text = format(Decimal(repr(value)).normalize(), "f")
    return "0" if text in ("-0", "0") else text


def _metric(value: float, digits: int) -> str:
    magnitude = abs(value)
    if magnitude != 0 and (magnitude < _SMALLEST_PLAIN or magnitude >= _LARGEST_PLAIN):
        mantissa, exponent = f"{value:.{max(digits - 1, 0)}e}".split("e")
        return f"{_plain(float(mantissa))} × 10{str(int(exponent)).translate(_SUPERSCRIPT)}"
    return _plain(float(f"{value:.{digits}g}"))
