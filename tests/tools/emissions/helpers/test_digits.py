"""Tests for tools.emissions.helpers.digits."""

from __future__ import annotations

import pytest

from tools.emissions.helpers.digits import digit_string


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("123", "123"),
        (" 123 ", "123"),
        (123, "123"),
        ("0123", "0123"),  # leading zeros are part of the identifier
        (0, "0"),
        ("", None),
        ("  ", None),
        ("12a", None),
        ("1.5", None),
        ("-1", None),
        ("٣٠", None),  # non-ASCII digits
        (True, None),
        (-5, None),
    ],
)
def test_digit_string(value: str | int, expected: str | None) -> None:
    assert digit_string(value) == expected
