"""Tier 1 lookup: FRS ID -> EIS IDs -> NEI stack candidates."""

from __future__ import annotations

from collections.abc import Mapping

from config.efservice import FrsSettings
from config.stack import StackSettings
from tools.emissions.helpers.efservice import EfserviceClient
from tools.emissions.helpers.stack.frs import eis_ids_for_frs
from tools.emissions.helpers.stack.nei import Candidates, Stack, build_candidates
from tools.schemas import NeiStackResult, StackParameters

SCC_TOOL = "fetch_stack_parameters_from_scc"


def _candidate(stack: Stack) -> StackParameters:
    return StackParameters(
        stack_height=stack["stack_height"],
        stack_diameter=stack["stack_diameter"],
        exit_velocity=stack["exit_velocity"],
        exit_temperature=stack["exit_temperature"],
        source="NEI",
        scc=None,
        warnings=[],
    )


def _result(eis_ids: tuple[str, ...], found: Candidates, warnings: list[str]) -> NeiStackResult:
    if not found.stacks:
        warnings = [*warnings, f"no NEI stack values were found; use {SCC_TOOL} instead"]
    return NeiStackResult(
        eis_ids=list(eis_ids),
        candidates=[_candidate(stack) for stack in found.stacks],
        total_candidates=found.total,
        warnings=warnings,
    )


def nei_stack_result(
    frs_id: str | int,
    client: EfserviceClient,
    frs: FrsSettings,
    settings: StackSettings,
    aliases: Mapping[str, str] | None,
) -> NeiStackResult:
    """Return the NEI stack candidates of the facility with this FRS ID.

    Args:
        frs_id: FRS ID as text or a non-negative integer.
        client: Envirofacts client (injected).
        frs: FRS-to-EIS query settings.
        settings: Stack settings (NEI table, units, ranges).
        aliases: Unit spelling -> Pint-parsable unit string.

    Returns:
        Candidates in m, m, m/s and K with warnings. When the FRS ID is invalid, has no EIS
        ID, or the NEI has no usable stack, ``candidates`` is empty and a warning says so.
        Data and network problems never raise.

    Raises:
        ValueError: If the configuration is unusable.
    """
    lookup = eis_ids_for_frs(frs_id, client, frs)
    warnings = list(lookup.warnings)
    if not lookup.eis_ids:
        return _result((), Candidates((), 0, ()), warnings)
    found = build_candidates(lookup.eis_ids, settings, aliases)
    return _result(lookup.eis_ids, found, [*warnings, *found.warnings])
