"""A small time-limited cache that hands out copies, so callers never share its values."""

from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Hashable


class TtlCache[K: Hashable, V]:
    """Keeps up to ``max_entries`` values for ``ttl_seconds`` each; thread-safe.

    ``get`` and ``put`` copy the value (deep), so a cached value cannot be changed through
    what was stored or what was returned. A ``ttl_seconds`` of 0 keeps nothing.
    """

    def __init__(
        self,
        ttl_seconds: float,
        max_entries: int = 8,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds < 0 or max_entries < 1:
            raise ValueError("ttl_seconds must be >= 0 and max_entries >= 1")
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._entries: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        """A copy of the value stored under ``key``, or None when absent or expired."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            stored_at, value = entry
            if self._clock() - stored_at >= self._ttl:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return copy.deepcopy(value)

    def put(self, key: K, value: V) -> None:
        """Store a copy of ``value``; the oldest entry goes when the cache is full."""
        if self._ttl == 0:
            return
        with self._lock:
            self._entries[key] = (self._clock(), copy.deepcopy(value))
            self._entries.move_to_end(key)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        """Forget every entry."""
        with self._lock:
            self._entries.clear()
