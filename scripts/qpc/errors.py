"""Errors of the QPC baseline build; each stops the run before anything is written."""

from __future__ import annotations


class QpcError(Exception):
    """Base of every error that makes the build refuse to write the baseline."""


class QpcDownloadError(QpcError):
    """The workbook could not be fetched or is not a workbook."""


class QpcLayoutError(QpcError):
    """The workbook is not the release or the layout that was asked for."""


class QpcDataError(QpcError):
    """The workbook was read but its values are not enough to trust."""


class RowSkipped(Exception):  # noqa: N818  # control flow for one row, not a failure of the run
    """One row cannot be attributed to whole four-digit codes; ``reason`` says why."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
