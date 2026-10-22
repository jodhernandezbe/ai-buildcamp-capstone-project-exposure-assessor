"""Which QPC release to download: the quarter a fixed number of quarters before today."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

QUARTERS_PER_YEAR = 4
MONTHS_PER_QUARTER = 3


@dataclass(frozen=True)
class Release:
    """A QPC release: calendar ``year`` and ``quarter`` (1-4)."""

    year: int
    quarter: int

    @property
    def label(self) -> str:
        """The release as ``2026Q2``."""
        return f"{self.year}Q{self.quarter}"


def release_for(today: date, lag_quarters: int) -> Release:
    """The release ``lag_quarters`` quarters before the quarter containing ``today``."""
    if lag_quarters < 0:
        raise ValueError("lag_quarters must be >= 0")
    index = today.year * QUARTERS_PER_YEAR + (today.month - 1) // MONTHS_PER_QUARTER - lag_quarters
    return Release(index // QUARTERS_PER_YEAR, index % QUARTERS_PER_YEAR + 1)


def release_url(template: str, release: Release) -> str:
    """Fill the ``{year}`` and ``{quarter}`` slots of the URL template."""
    return template.format(year=release.year, quarter=release.quarter)
