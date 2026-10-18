"""Find the EIS facility ID of a facility from its FRS ID (the NEI's key)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import quote

from config.efservice import FrsSettings
from tools.digits import digit_string
from tools.emissions.helpers.efservice import EfserviceClient, EfserviceError, Row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EisLookup:
    """The EIS IDs found for an FRS ID.

    Attributes:
        frs_id: The FRS ID as queried (digits only), or None if the input was not one.
        eis_ids: Distinct EIS facility IDs in response order; empty when none was found.
        warnings: Why no ID was found (blank for success).
    """

    frs_id: str | None
    eis_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def _eis_id(row: Row, frs_id: str, settings: FrsSettings) -> str | None:
    """Return the row's EIS ID if the row is the EIS registration of ``frs_id``."""
    registry = row.get(settings.registry_field)
    program = row.get(settings.program_field)
    if str(registry).strip() != frs_id or str(program).strip().upper() != settings.program.upper():
        return None
    value = row.get(settings.eis_id_field)
    return digit_string(value) if isinstance(value, str | int) else None


def _distinct_ids(rows: list[Row], frs_id: str, settings: FrsSettings) -> tuple[str, ...]:
    found = (_eis_id(row, frs_id, settings) for row in rows)
    return tuple(dict.fromkeys(eis for eis in found if eis is not None))


def eis_ids_for_frs(
    frs_id: str | int,
    client: EfserviceClient,
    settings: FrsSettings,
) -> EisLookup:
    """Look up the EIS facility IDs registered for an FRS ID.

    Args:
        frs_id: FRS (registry) ID as text or a non-negative integer.
        client: Envirofacts client (injected).
        settings: FRS query settings.

    Returns:
        The distinct EIS IDs, or none plus a warning when the FRS ID is not valid, the
        facility has no EIS registration, or the request failed. Rows for another registry
        ID or program, or without a digit-string ID, are ignored. Never raises on data or
        network problems.
    """
    digits = digit_string(frs_id)
    if digits is None:
        return EisLookup(None, (), (f"FRS ID {frs_id!r} is invalid: it must be digits only",))
    path = settings.eis_path.format(frs_id=quote(digits, safe=""))
    try:
        rows = client.get_rows(path)
    except EfserviceError as exc:
        logger.warning("EIS lookup for FRS ID %s failed: %s", digits, exc)
        return EisLookup(digits, (), (f"the EIS ID of FRS ID {digits} could not be looked up",))
    ids = _distinct_ids(rows, digits, settings)
    if not ids:
        return EisLookup(digits, (), (f"FRS ID {digits} has no {settings.program} registration",))
    return EisLookup(digits, ids)
