"""Longest-prefix lookup in a mapping keyed by strings (e.g. hierarchical codes)."""

from __future__ import annotations

from collections.abc import Mapping


def longest_prefix[V](table: Mapping[str, V], key: str, *, min_length: int) -> tuple[str, V] | None:
    """Return the entry whose key is the longest prefix of ``key`` (``key`` itself included).

    Prefixes are tried from ``len(key)`` down to ``min_length`` characters, so the most
    specific entry wins, using one dictionary probe per length (no scan of ``table``). Entries
    longer than ``key`` are never matched.

    Args:
        table: Entry key -> value.
        key: The string to match.
        min_length: Shortest prefix to try; at least 1.

    Returns:
        ``(matched key, value)``, or None when no prefix of at least ``min_length`` is in
        ``table`` (including when ``key`` is shorter than ``min_length``).

    Raises:
        ValueError: If ``min_length`` is below 1.
    """
    if min_length < 1:
        raise ValueError("min_length must be at least 1")
    for length in range(len(key), min_length - 1, -1):
        prefix = key[:length]
        if prefix in table:
            return prefix, table[prefix]
    return None
