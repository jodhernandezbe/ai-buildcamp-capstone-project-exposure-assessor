"""A secret visible only to the code running inside a ``with`` block of the current context.

Backed by a ``ContextVar``, so it follows asyncio tasks and the executor threads LangChain
and LangGraph start from them, and concurrent requests never see each other's value. The
secret is never written to the process environment.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import SecretStr


class ScopedSecret:
    """Holds at most one secret per context; empty outside ``provide``."""

    def __init__(self, name: str) -> None:
        self._var: ContextVar[SecretStr | None] = ContextVar(name, default=None)

    def get(self) -> SecretStr | None:
        """Return the secret provided to the current context, or None."""
        return self._var.get()

    @contextmanager
    def provide(self, secret: SecretStr) -> Generator[None]:
        """Make ``secret`` visible to the current context until the block exits.

        Cleared with ``set(None)`` rather than ``reset(token)``: an async generator can be
        closed from a different context (a client disconnect), where a token is invalid.
        """
        self._var.set(secret)
        try:
            yield
        finally:
            self._var.set(None)
