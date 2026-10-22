## Context

The agent drives the exposure chain one tool call at a time. For one facility that is fine;
for the 25 the inventory lists it is ~100 calls, and the exposure call repeats every input.
gpt-4.1 truncates such fan-outs (Oct 19 evals; Oct 21 live run: 3 of 25).

## Goals / Non-Goals

- Goals: every listed facility assessed in one call; a stack for every facility (generic as
  the last resort, labelled); the same evidence order and labels as the single tools; no change
  to the prompt's "names no tool" rule.
- Non-goals: removing the single tools; changing the science of any step; persisting results.

## Decisions

- **Compose the tools, don't reimplement them.** Each step is the single tool invoked with the
  same arguments (`Steps` makes them injectable for tests). The tools' edges (clients, keys,
  clock) and contracts (never raise on data/network problems, label defaults) carry over
  unchanged. This is the one place a tool imports other tool folders; `tools/CLAUDE.md` records
  the exception (only the registry imports `tools/assessment/`).
- **Stack order in code.** NEI candidates (the inventory's `eis_ids`) -> PSTK stacks of SCC
  matches at or above `scc_min_score`, distinct values only, at most `max_scc_stacks` (a range,
  as the prompt asks for credible alternatives) -> AirToxScreen global default. The floor 0.55
  was set from live scores: soybean oil processing ~0.69, rubber ~0.73, refineries ~0.65, while
  "Railroad Rolling Stock Manufacturing" -> "Stamping" scores 0.47. Each fall-back notes why.
- **Concurrency.** A thread pool of `max_workers` (4); each task runs in
  `contextvars.copy_context()` so the per-run keys (Census, CompTox, provider) reach it. The SCC
  index (Chroma) is not safe to open from several threads, so the SCC step takes a lock.
- **Selection.** Default: the facilities the inventory lists (`shown`), capped at
  `max_facilities`; `frs_ids` picks particular facilities from the whole matching list (EIS IDs
  are resolved for any never resolved). Missing and capped facilities are reported.
- **Benchmarks.** `toxicity` (e.g. a read-across surrogate's) is used as given; otherwise the
  chemical's own from CompTox, keeping only the RfC/IUR warnings.
- **Two views.** `content_and_artifact`: the model reads a compact summary (≈30 kB for 25
  facilities), the workspace reads the full chain per facility.
- **Inventory reuse.** A thread-safe TTL cache (`commons/ttl_cache.py`, deep copies in and out)
  keyed by CAS, place and year. Tests clear it in `tests/conftest.py`.
- **Attribution by FRS ID.** Exposure items may carry an FRS ID instead of an emission rate;
  everything else is filed exactly like the single tools' results, so "latest wins" still holds.

- **Tiered screening, not a rank cut.** EPA's tiered approach: exclude only on a conservative
  bound. Tier 1 multiplies a unit-rate worst case (global default stack: 3 m, 0.2 m, 4 m/s,
  295 K; SCREEN3 54 combinations; the highest over `screening.ambient_temperatures_k`, since a
  hot day removes the buoyant rise of a cold stack) by each emission rate: concentration, HQ and
  risk are linear in the rate, so one calculation bounds 1231 facilities. The bound assumes a
  person at the maximum, so a facility screened out cannot be one with people nearby.
  Thresholds 0.1 HQ (room for other chemicals at the same site) and 1e-6 cancer risk.
- **Tier 2 needs no weather or Census.** The worst case does not use site weather (only the
  ambient temperature, taken at its most conservative), so the own-stack worst case of ~300
  facilities costs only the EIS, NEI and SCC lookups. Its representative ranges are dropped
  (they would reflect the synthetic weather).
- **Tier 3 is capped by the weather quota.** One year of hourly ERA5 is ~26 Open-Meteo calls
  (7 variables, 365 days); the free tier allows 600 a minute and 5000 an hour, so the full chain
  stays at `max_facilities` (25), chosen by own-stack worst-case risk. Facilities in one
  0.25-degree cell share the request (ERA5 is a 0.25-degree grid, so the series is the same).
- **EIS lookup at scale.** 260 unresolved facilities took 802 s (one throttled twin search
  and one registration request each, in sequence). Twin searches now run `twin_workers` at a
  time (the HTTP client keeps no per-request state; httpx clients are thread-safe), the twins'
  registrations are read in one bulk request, and results are reused for `cache_seconds`.
- **Artifact.** A dict with `assessed` (full and worst-case-only chains) and `screened_out`
  (records with bounds); the projector still accepts the earlier list form.

## Risks / Trade-offs

- The bound uses a 3 m stack; a release lower than that (fugitive) could exceed it. TRI's
  `AIR STACK` medium is the one assessed; the limitation is stated in the notes.
- Worst-case-only facilities have no residents count; their HQ is at the screening maximum,
  which may fall where no one lives (stated).
- A national run is longer (inventory ~40 s, refinement ~1-2 min, full chain ~30 s).

- One long tool call (≈1–2 min for 25 facilities) with no per-step progress events. Accepted:
  one step label covers it.
- Less model judgment in the default path (the SCC choice is a rule). The single tools remain
  for overrides the user asks for.
- Eval cassettes must be re-recorded.
