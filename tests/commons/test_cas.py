"""Tests for commons.cas."""

from __future__ import annotations

import pytest

from commons.cas import format_cas


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("71-43-2", "71-43-2"),
        ("108-88-3", "108-88-3"),
        ("7732-18-5", "7732-18-5"),
        ("50-00-0", "50-00-0"),
        ("71432", "71-43-2"),
        ("  71-43-2  ", "71-43-2"),
        ("\t56-23-5\n", "56-23-5"),
        ("7647145", "7647-14-5"),
    ],
)
def test_valid_cas_is_normalized(raw: str, expected: str) -> None:
    assert format_cas(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "71-43-3",  # wrong check digit
        "0-00-0",  # first group too short
        "71-43",
        "7-143-2",  # misplaced hyphen
        "71-43-22",
        "71--43-2",
        "abc-de-f",
        "71-43-2; DROP",
        "7143",  # too few digits
        "12345678901",  # too many digits
        "71 43 2",
        "-71-43-2",
        "７１-４３-２",  # non-ASCII digits
    ],
)
def test_invalid_cas_is_rejected(raw: str) -> None:
    assert format_cas(raw) is None
