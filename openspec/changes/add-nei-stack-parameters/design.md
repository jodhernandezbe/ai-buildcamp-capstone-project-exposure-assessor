## Context

See proposal.md. Tier 2 (`fetch_stack_parameters_from_scc`, archived change `add-stack-tiers-and-scc-context`) already has the building blocks reused here: `config/stack.py` (typed `[stack]` settings, ranges, target units), `tools/emissions/helpers/stack_values.py` (one row -> four SI values or reasons) and the cached-CSV reading pattern of `pstk.py`.

Facts measured on the 2023 NEI SMOKE point flat file (FF10_POINT; 11.76 M rows, 4.0 GB; `data/raw/nei_smoke_point_2023.zip`):
- One row per pollutant and process; stack fields repeat unchanged. 664,543 release points (`FACILITY_ID`, `UNIT_ID`, `REL_POINT_ID`) at 99,186 facilities. `FACILITY_ID` is the EIS ID: all digits, 3 to 8 digits (68% have 8), no leading zeros.
- Within a release point the four stack values never differ across rows, so a "newest record" step changes nothing (some release points carry several `DATE_UPDATED` values and a 2021 `CALC_YEAR`, with the same stack values). The file is effectively one inventory year.
- 46% of release points are fugitive (no stack fields). 353,796 release points at 52,726 facilities have all four values positive; 57,000 have a zero velocity. A facility has exactly one NAICS.
- Distinct (EIS ID, four values) rows: 202,181. Facilities with more than one distinct combination: 29,845 of 52,726 (median 2, p90 7, p99 35, max 340).
- Values are in ft, ft, degF and ft/s (SMOKE FF10 convention; the sample values are consistent with it).
- Of 40 sampled TRI facilities, FRS_PROGRAM_FACILITY gave 21 one EIS ID, 2 two, 16 none, 1 server error.

## Goals / Non-Goals

**Goals:**
- Facility-specific stack candidates by FRS ID from a committed local table, fail closed, units converted with Pint.
- Expose the spread of real stacks (no invented "average stack"); keep the number of scenarios manageable.
- One shared Envirofacts client; configuration-only changes for a new NEI vintage or column naming.

**Non-Goals:**
- Downloading the NEI automatically, or using NEI emissions, locations or pollutants (TRI covers emissions).
- Choosing one release point or ranking stacks by emissions or dispersion model output; the agent evaluates every candidate.
- NAICS or SCC filtering of stacks (one NAICS per facility; SCC is the tier 2 key).
- Combining values from different release points.

## Decisions

**D0. Two-step key: FRS ID -> EIS IDs -> NEI rows.** `FRS_PROGRAM_FACILITY` (filter `REGISTRY_ID/{frs_id}/PGM_SYS_ACRNM/EIS`) returns the program rows linking them; the EIS ID is `pgm_sys_id`. A facility can have several (co-located operators, reissued permits); all distinct IDs are used and those without rows in the NEI table simply contribute nothing. No ID, a failure or a bad response is a data problem: no candidates plus a warning (fail closed). Rows whose `registry_id` or `pgm_sys_acrnm` do not match the request are dropped. (Implemented: `helpers/frs.py`.)

**D0b. Envirofacts access: shared transport, separate queries.** `helpers/efservice.py` (`EfserviceClient.get_rows(path)`) owns throttling, retry/backoff, `Retry-After`, timeout and the "JSON list of objects" check for TRI and FRS; `[efservice]` holds base URL and policy. Each query keeps its own path template and parameters (`[tri]`, `[frs]`). Error type: `EfserviceError`. (Implemented.)

**D1. Sharded gzip CSV, committed.** The table has one row per (EIS ID, four values) and is split into files by the first `prefix_digits` digits of the EIS ID (default 1: nine shards of 56 to 389 KB gzipped, 1.4 MB in all). A lookup reads only the shard for its ID prefix and caches it by path and modification time (like PSTK). An unreadable or missing shard is a data problem (warning, no candidates); a missing configured column is a setup error and raises. SQLite was rejected: a binary file cannot be committed under the size limit either and adds nothing a single small shard does not.

**D2. EIS ID is the key, exact digit string.** Whitespace is removed and nothing else changed; it is compared and sharded as text. Non-digit IDs are never looked up.

**D3. Candidates, not a pick.** All rows of the facility's EIS IDs are converted and validated through `stack_values` (reused, so ranges match tier 2: non-finite, boolean, non-positive and out-of-range values count as missing; a row with any missing value is dropped, never repaired). Valid rows are merged when equal after rounding every value to `merge_significant_digits` significant digits (the first row's actual values are kept; nothing is averaged), then ordered lowest stack height first (ties: lowest exit velocity, exit temperature, then diameter) and the first `max_candidates` are returned. The warnings state how many valid, distinct combinations existed, how many were merged and how many were omitted, and which rule ordered them. Lowest first is the conservative order for ground-level concentrations at a screening level, and is deterministic.

**D4. Result shape.** A new `NeiStackResult` TypedDict: `eis_ids`, `candidates` (a `StackParameters` per candidate: source "NEI", scc None, its own empty warnings), `total_candidates` (before the cap) and `warnings`. The NEI tool never returns the global default: with no candidates the description tells the LLM to call the SCC tool.

**D5. Compact table script.** `scripts/compact_nei_stacks.py` streams the member CSV of the raw zip (skipping `#` header lines), keeps the configured raw columns, drops rows whose ID is not a digit string or whose four values are not finite and positive, dedupes (ID, four values as text, normalised so `23` and `23.0` are equal), and writes deterministic gzip shards (`mtime=0`, sorted). Stale shards matching the template are removed first. Memory stays small (only distinct rows are held). Raw column names live in `[stack.nei.raw_columns]`, not in the code.

**D6. Settings.** `[stack.nei]`: `directory`, `file_template` (contains `{prefix}`), `prefix_digits`, `id_column`, `columns`, `units`, `max_candidates`, `merge_significant_digits`, `raw_path` and `raw_columns`. Ranges and target units stay under `[stack]`.

## Risks / Trade-offs

- [The units are not what the sample suggests] -> Units are config; the first lookups are checked against the plausible ranges and a test uses real-shaped conversions; the README states the assumption (SMOKE FF10: ft, ft, degF, ft/s).
- [Many scenarios for the agent] -> The cap bounds it, near-duplicates merge, and the warnings say how many were left out.
- [Lowest-first cap hides tall stacks] -> Documented; tall stacks are the less conservative ones, and the omitted count is reported.
- [Co-located operators with different EIS IDs mix their stacks] -> Both are real stacks at the site; the candidates are not combined and the agent sees them all (within the cap).
- [A larger future NEI makes shards too big] -> `prefix_digits` is a setting; the script rewrites the shards.
- [Facilities without any valid stack (47%)] -> They return no candidates and the SCC tool is the fallback by design.
