"""Plain-language messages for the model provider's failures, safe to show the user.

The provider's own message is never shown (it can echo request details); each failure maps to
one fixed message. The provider package is not imported: a failure is recognised by what it
carries (an HTTP ``status_code`` and an error ``code``) and by the names of its classes.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

OUT_OF_CREDITS = (
    "Your OpenAI account has no credits left. Add credits in your OpenAI billing settings "
    "(platform.openai.com), then try again."
)
BAD_KEY = "OpenAI rejected the API key. Check or replace it in Settings (the gear icon)."
RATE_LIMITED = "OpenAI is limiting requests right now. Wait a moment and try again."
UNREACHABLE = "Could not reach OpenAI. Check your connection and try again."
PROVIDER_DOWN = "OpenAI is having trouble right now. Try again in a little while."
FORBIDDEN = "OpenAI refused the request for this account or model. Check your OpenAI account."

_NO_CREDIT_CODES = frozenset({"insufficient_quota", "credit_balance_exhausted"})
_NETWORK_FAILURES = frozenset({"APIConnectionError", "APITimeoutError", "ConnectTimeout"})
_HTTP_UNAUTHORIZED, _HTTP_FORBIDDEN, _HTTP_RATE_LIMITED, _HTTP_SERVER_ERROR = 401, 403, 429, 500


def _codes(exc: BaseException) -> set[str]:
    """The error codes the failure carries, as the provider's SDK exposes them."""
    found = {getattr(exc, "code", None)}
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        outer = cast(Mapping[str, object], body)
        error = outer.get("error", outer)
        if isinstance(error, dict):
            found.add(cast(Mapping[str, object], error).get("code"))
    return {code for code in found if isinstance(code, str)}


def _status(exc: BaseException) -> int | None:
    status = getattr(exc, "status_code", None)
    return status if isinstance(status, int) and not isinstance(status, bool) else None


def explain(exc: BaseException) -> str | None:
    """A fixed, user-facing message for a provider failure, or None when it is not one."""
    status = _status(exc)
    if status == _HTTP_RATE_LIMITED:
        return OUT_OF_CREDITS if _codes(exc) & _NO_CREDIT_CODES else RATE_LIMITED
    if status == _HTTP_UNAUTHORIZED:
        return BAD_KEY
    if status == _HTTP_FORBIDDEN:
        return FORBIDDEN
    if status is not None and status >= _HTTP_SERVER_ERROR:
        return PROVIDER_DOWN
    if any(cls.__name__ in _NETWORK_FAILURES for cls in type(exc).__mro__):
        return UNREACHABLE
    return None
