## Why

`fetch_stack_parameters_from_nei` is the first-choice (tier 1) source of stack height, diameter, exit velocity and exit temperature, but it is still a stub, so every assessment currently falls through to generic SCC defaults. Facility-specific release-point data from the EPA National Emissions Inventory (NEI) gives dispersion the facility's own stacks. The NEI identifies facilities by EIS ID, not FRS ID, and a facility usually has several stacks, so the tool must resolve the ID and expose the real spread of stacks instead of guessing one.

## What Changes

- Implement `fetch_stack_parameters_from_nei(frs_id)`: FRS ID -> EIS facility IDs (Envirofacts `FRS_PROGRAM_FACILITY`) -> distinct stack combinations from a local NEI table, converted with Pint to m, m, m/s and K and checked against the plausible ranges (fail closed).
- Return **candidates**, not one pick: the distinct combinations of the four values (identical release points collapse, near-identical ones merge), lowest stack first, capped at a configured number with a warning of how many were omitted. Values are never combined across release points; every candidate is a real record. The agent is told to evaluate exposure for every candidate and report the range.
- A facility with no EIS ID, no stacks in the NEI, or only invalid values returns no candidates and a warning pointing to `fetch_stack_parameters_from_scc`.
- Resolve the EIS ID with a helper over the Envirofacts `FRS_PROGRAM_FACILITY` table. A sample of 40 TRI facilities had 21 with one EIS ID, 2 with two, 16 with none.
- Centralize Envirofacts access: one `[efservice]` table (base URL, delay, timeout, retries, backoff) and one HTTP client (throttle, retry, JSON list check) shared by the TRI fetcher and the FRS lookup. Endpoint paths and paging stay with each concern (`[tri]`, `[frs]`). **BREAKING (internal):** `base_url`, `delay_seconds`, `timeout_seconds`, `max_retries` and `backoff_seconds` move from `[tri]` to `[efservice]`.
- Add a compact NEI table: the 2023 NEI SMOKE point flat file (4 GB, 77 columns, one row per pollutant and process) reduces to the distinct EIS ID + four stack values (about 200,000 rows). A script builds it from the raw zip into gzip CSV shards named by the leading digit(s) of the EIS ID, each below the 1,000 KB large-file limit, so the shards can be committed and a lookup reads one small shard.
- Add `[stack.nei]` settings (shard directory and file template, prefix digits, columns, reported units ft/ft/degF/ft/s, candidate cap, merge precision, raw-file location and raw column names) with a typed loader.
- NAICS is not used: a facility has one NAICS in the NEI file, so it cannot separate its stacks, and TRI rows carry none.

## Capabilities

### New Capabilities
- `efservice-access`: the shared, throttled, retrying Envirofacts client and its `[efservice]` settings.
- `eis-facility-lookup`: FRS ID -> EIS facility ID(s) through `FRS_PROGRAM_FACILITY`, with `[frs]` settings.
- `nei-stack-table`: the compact, sharded NEI stack table and the script that builds it from the raw SMOKE file.
- `stack-parameters-nei`: tier 1 stack candidates by FRS ID (spec moved here from the archived `add-stack-tiers-and-scc-context`, now candidate-based).

### Modified Capabilities
- `app-configuration`: new `[efservice]`, `[frs]` and `[stack.nei]` settings; the TRI settings requirement no longer owns the base URL and request policy.
- `emissions-inventory-tool`: the TRI fetcher uses the shared client (retry/throttle behavior unchanged).

## Impact

- Code: `tools/emissions/stack.py` (the NEI tool and its result type in `tools/schemas.py`), new `tools/emissions/helpers/{efservice,frs,digits,nei}.py`, `tools/emissions/helpers/tri.py` (uses the shared client), `config/` (`efservice` and `stack` loaders, `settings.toml`), `scripts/compact_nei_stacks.py`.
- Data: `data/nei_stacks/nei_stacks_{1..9}.csv.gz` (about 1.4 MB in total, each shard below 400 KB); the raw `nei_smoke_point_2023.zip` (265 MB) stays in git-ignored `data/raw/`.
- Tests: helper, tool, settings and script tests with synthetic fixtures (fake IDs, round numbers; no real data).
- Dependencies: none.
