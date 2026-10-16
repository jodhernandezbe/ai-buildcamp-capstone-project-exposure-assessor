"""CAS registry number validation and normalization."""

from __future__ import annotations

import re

_HYPHENATED = re.compile(r"\d{2,7}-\d{2}-\d", re.ASCII)
_BARE = re.compile(r"\d{5,10}", re.ASCII)


def format_cas(raw: str) -> str | None:
    """Validate a CAS registry number and return it in hyphenated form.

    Accepts the hyphenated form ("71-43-2") or bare digits ("71432"), with surrounding
    whitespace. The check digit is verified: the digits before it, weighted 1, 2, 3, ...
    from the right, must sum to the check digit modulo 10.

    Args:
        raw: Candidate CAS registry number.

    Returns:
        The hyphenated CAS number ("NNNNNNN-NN-N"), or None if ``raw`` is not a valid one.
    """
    candidate = raw.strip()
    if not (_HYPHENATED.fullmatch(candidate) or _BARE.fullmatch(candidate)):
        return None
    digits = candidate.replace("-", "")
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * weight for weight, d in enumerate(reversed(body), start=1))
    if total % 10 != check:
        return None
    return f"{body[:-2]}-{body[-2:]}-{check}"
