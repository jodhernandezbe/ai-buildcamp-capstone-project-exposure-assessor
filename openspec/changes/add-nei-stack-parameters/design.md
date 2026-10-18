## Context

See proposal.md. Tier 2 (`fetch_stack_parameters_from_scc`, archived change `add-stack-tiers-and-scc-context`) already has the building blocks this reuses: `config/stack.py` (typed `[stack]` settings, ranges, target units, global fallback), `tools/emissions/helpers/stack_values.py` (one row -> four SI values or warnings), and `tools/emissions/helpers/pstk.py` (cached CSV reader keyed by file and modification time). `StackParameters` already has nullable values plus `source`, `scc` and `warnings`. The NEI tool is a stub (`raise NotImplementedError`) with a finished description. The `stack-parameters-nei` spec is in this change, moved from the archived one.

The NEI file is not in the repo yet; the user will supply it. Decisions below that depend on its columns are marked and resolved in task 1.

## Goals / Non-Goals

**Goals:**
- Facility-specific stack values by FRS ID from a local file, fail closed, units converted with Pint.
- Same configuration style as PSTK so a different NEI vintage or column naming is a config edit.
- No network, no new dependencies.

**Non-Goals:**
- Downloading or refreshing NEI data, or converting raw NEI files (a one-off conversion to CSV, as was done for PSTK).
- Combining several release points into one set of values, or emissions-weighted selection.
- Using NEI emissions or location fields (the TRI tool covers those).
- Per-process (SCC) selection among a facility's release points.

## Decisions

**D1. Local CSV, read once and cached.** The file is read with stdlib `csv` and indexed by FRS ID, re-read when the file or the settings change, exactly like PSTK (`_cached_table`). A missing or unreadable file is a data problem: all four values `None` plus a warning (the tier 2 tool is the fallback), not an exception. A missing configured column is a setup error and raises.

**D2. FRS ID is the key, exact match.** The FRS ID is a 12-digit identifier. As with SCC, it is compared as a digit string with surrounding whitespace removed and nothing else changed; an integer input is accepted and turned into its digit string. If the NEI file is keyed by the NEI's own facility identifier rather than FRS ID, the file needs an FRS column or a crosswalk; this is checked in task 1 before any code is written.

**D3. One release point, deterministic.** A facility's rows are release points. Among the rows with all four values valid, the tallest stack wins; ties break by file order. A warning states how many release points were found and the rule used. Values are never mixed across release points. If none is fully valid, all four values are `None` with a warning naming the invalid fields of the tallest row.

**D4. Reuse `stack_values`.** Parsing, Pint conversion and range checking of a row go through the existing helper with the NEI columns and units, so range behavior is identical across tiers (non-finite, boolean, non-positive and out-of-range values count as missing).

**D5. Result shape.** `source` is "NEI", `scc` is `None`, `warnings` explains selection or absence. The NEI tool never returns the global default: when it has no values it returns `None` fields and the description tells the LLM to call the SCC tool.

**D6. Settings.** `[stack.nei]` mirrors `[stack.pstk]`: `path`, `facility_id_column`, `columns` (quantity -> column) and `units` (quantity -> reported unit). Plausible ranges and target units stay under `[stack]`.

## Risks / Trade-offs

- [The NEI file's identifiers or layout differ from the assumptions] -> Task 1 inspects the real file first; D2 and D6 are adjusted before implementation.
- [A large file is slow to load or too big to commit] -> It is read once and cached; a size above the hook limit stays uncommitted (as with the SCC table) and the README says where to put it.
- [Taller is not always the main stack] -> It is a documented, deterministic screening rule and the warning reports the count; weighting by emissions needs data this tool does not have.
- [Zeros or placeholders in the file] -> Treated as invalid by the range check, so such facilities return `None` and the SCC tool is used (same trade-off as PSTK).
