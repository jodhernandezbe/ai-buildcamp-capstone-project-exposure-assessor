"""Stack parameter lookup tools: tier 1 (NEI, by facility) and tier 2 (PSTK, by SCC)."""

from __future__ import annotations

from langchain_core.tools import tool

from config.loader import get_unit_settings
from config.stack import get_stack_settings
from tools.emissions.helpers.pstk import scc_stack_parameters
from tools.schemas import StackParameters


@tool
def fetch_stack_parameters_from_nei(frs_id: str) -> StackParameters:
    """Fetch a facility's own release-point (stack) geometry and exit conditions from the NEI.

    Purpose:
        Plume rise and dispersion depend on stack geometry. This is the first choice for
        stack parameters: call it after identifying a facility. If it returns no values
        (all four are null), call `fetch_stack_parameters_from_scc` with the facility's
        SCC code instead.

    Args:
        frs_id: EPA Facility Registry Service identifier of the facility.

    Returns:
        A dict with:
        - stack_height: m above ground (null if not found)
        - stack_diameter: m (null if not found)
        - exit_velocity: m/s (null if not found)
        - exit_temperature: K (null if not found)
        - source: "NEI", or null if no values were found
        - scc: always null for this tool
        - warnings: why values are missing, or which release point was chosen
    """
    raise NotImplementedError


@tool
def fetch_stack_parameters_from_scc(scc_code: str | int | None = None) -> StackParameters:
    """Fetch generic default stack parameters for a process type (SCC); tier 2 fallback.

    Purpose:
        Use this ONLY after `fetch_stack_parameters_from_nei` returned no values (all four
        null) for the facility. The values are EPA PSTK (Point Source Stack Replacements)
        defaults for the kind of process identified by the SCC, not measurements of the
        facility's own stack. If no SCC is given, or the SCC is unknown or invalid, the EPA
        AirToxScreen global point-source default is returned instead (3.0 m height, 0.2 m
        diameter, 4.0 m/s, 295.4 K), so a result always has values. Get the SCC from
        `get_facility_metadata` or `lookup_scc_process_description`; if neither gives one,
        call this tool without `scc_code` to get the global default.

    Args:
        scc_code: Source Classification Code, digits only, e.g. "30600101", exactly as
            returned by `get_facility_metadata` or `lookup_scc_process_description` (a number
            is also accepted). Omit it (or pass null) when the facility's SCC is not known.

    Returns:
        A dict with:
        - stack_height: m above ground
        - stack_diameter: m
        - exit_velocity: m/s
        - exit_temperature: K
        - source: "PSTK" (SCC-specific default) or "AirToxScreen global default" (generic
          fallback; state this to the user, as it is the least specific estimate)
        - scc: the SCC whose PSTK row was used, or null for the global default
        - warnings: why the global default was used (including "no SCC was given"), or
          notes on the PSTK row chosen
    """
    return scc_stack_parameters(scc_code, get_stack_settings(), get_unit_settings().aliases)
