"""Tests for scripts.qpc.release."""

from __future__ import annotations

from datetime import date

import pytest

from scripts.qpc.release import Release, release_for, release_url


@pytest.mark.parametrize(
    ("today", "lag", "expected"),
    [
        (date(2026, 10, 22), 2, Release(2026, 2)),
        (date(2026, 4, 1), 2, Release(2025, 4)),
        (date(2026, 6, 30), 2, Release(2025, 4)),
        (date(2026, 1, 1), 2, Release(2025, 3)),
        (date(2026, 12, 31), 2, Release(2026, 2)),
        (date(2026, 7, 1), 0, Release(2026, 3)),
        (date(2026, 1, 15), 4, Release(2025, 1)),
    ],
)
def test_release_is_lag_quarters_back(today: date, lag: int, expected: Release) -> None:
    assert release_for(today, lag) == expected


def test_negative_lag_is_rejected() -> None:
    with pytest.raises(ValueError, match="lag_quarters"):
        release_for(date(2026, 1, 1), -1)


def test_url_and_label() -> None:
    release = Release(2025, 4)
    assert release.label == "2025Q4"
    assert (
        release_url("https://h/{year}/{year}-q{quarter}.xlsx", release)
        == "https://h/2025/2025-q4.xlsx"
    )
