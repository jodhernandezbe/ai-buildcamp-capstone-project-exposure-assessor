"""Identifiers made of digits (SCC, FRS ID, EIS ID) compared as exact digit strings."""

from __future__ import annotations

import re

_DIGITS = re.compile(r"[0-9]+")


def digit_string(value: str | int) -> str | None:
    """Return ``value`` as a digit string, or None if it is not one.

    Whitespace around a string is ignored. Nothing else is changed: these identifiers have a
    fixed length, so one with an extra leading zero is a different identifier. An integer is
    accepted for callers that pass the identifier as a number; a boolean or negative integer
    is not an identifier. Only ASCII digits count.
    """
    if isinstance(value, bool) or (isinstance(value, int) and value < 0):
        return None
    text = str(value).strip()
    return text if _DIGITS.fullmatch(text) else None
