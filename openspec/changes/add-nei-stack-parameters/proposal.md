## Why

`fetch_stack_parameters_from_nei` is the first-choice (tier 1) source of stack height, diameter, exit velocity and exit temperature, but it is still a stub, so every assessment currently falls through to generic SCC defaults. Facility-specific release-point data from the EPA National Emissions Inventory (NEI) gives dispersion the facility's own stack.

## What Changes

- Implement `fetch_stack_parameters_from_nei(frs_id)` over a local NEI point-source release-point file in `data/` (converted to CSV, read offline, no network), following the same pattern as the PSTK tier: configured path, columns and units, Pint conversion to m, m, m/s and K, plausible-range checks that fail closed.
- When a facility has several release points, return one release point (the tallest with all four values valid) and warn how many there were; never mix values across release points.
- A facility that is absent, or has no valid release point, returns all four values as `None` with a warning pointing to `fetch_stack_parameters_from_scc`.
- Add a `[stack.nei]` settings table (file path, FRS ID column, value columns, reported units, delimiter if needed) with a typed loader; plausible ranges and target units are the existing `[stack]` ones.
- Keep the NEI tool description telling the LLM it is the first choice and to fall back to the SCC tool when it returns no values.

## Capabilities

### New Capabilities
- `stack-parameters-nei`: tier 1 stack geometry and exit conditions from the NEI by FRS ID (spec moved here from the archived `add-stack-tiers-and-scc-context`).

### Modified Capabilities
- `app-configuration`: new `[stack.nei]` settings with validation (new requirement; existing ones unchanged).

## Impact

- Code: `tools/emissions/stack.py` (the NEI tool), a new `tools/emissions/helpers/nei.py`, reuse of `tools/emissions/helpers/stack_values.py`, `config/stack.py`, `config/settings.toml`.
- Data: a new NEI CSV in `data/`, supplied by the user; its size decides whether it can be committed (the large-file hook limit is 1,000 KB).
- Tests: `tests/tools/emissions/helpers/test_nei.py`, `tests/tools/emissions/test_stack.py`, `tests/config/test_stack_settings.py`, synthetic fixture CSVs (no real data in tests).
- Dependencies: none.
