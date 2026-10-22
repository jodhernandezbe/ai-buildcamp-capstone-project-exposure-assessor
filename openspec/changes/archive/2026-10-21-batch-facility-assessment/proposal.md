## Why

A live hexane run on 2026-10-21 listed 25 facilities and fetched stacks, weather and residents
for 23 of them, then ran the exposure calculation for only 3 and called them "representative".
The two facilities without NEI stacks got no stack at all. Every input of the exposure tool had
to be re-typed by the model per facility, and 23 such calls are more than gpt-4.1 writes in a
turn; the same truncation was measured in the Oct 19 evaluations for stacks, and wording did not
fix it. The fallback to a process-typical or generic stack was a three-step chain the model had
to drive by hand, so it was skipped.

### Selection bias (added 2026-10-21, after review)

The first version assessed the 25 facilities the inventory lists, the largest emitters of 1231
for hexane. Ranking by emission rate is not a defensible exclusion: a live check gave a
conservative bound (EPA global default stack, SCREEN3 worst-case weather, a person at the
maximum) of HQ >= 1 for 92 facilities and >= 0.1 for 283, and with their own stacks facilities
ranked 33rd, 39th and 46th by emissions reach worst-case HQs of 21.9, 19.4 and 16.0, above most
of the top 25. Low emitters next to people were dropped silently.

## What Changes

- New tool `assess_facilities(cas_number, frs_ids?, state?, city?, radius_km?, toxicity?)` in a
  new `tools/assessment/` package. For each listed facility (or the ones asked for), in code:
  stacks in evidence order (the facility's NEI stacks; else up to `max_scc_stacks` distinct PSTK
  stacks of the SCC processes matching its industry title with a score of at least
  `scc_min_score`; else the EPA global default, with the reason), the weather at the site, the
  residents around it and the exposure result over all its stacks. Facilities run
  `max_workers` at a time in the caller's context (so this run's keys reach every request). The
  model gets a compact summary (ranges, stack tier, notes; highest worst-case HQ first); the
  program gets every detail as the artifact.
- The steps are the existing single tools, invoked as they are; they stay registered for
  follow-ups about one facility.
- The inventory of a chemical (and place) is reused for `inventory_cache_seconds`, so listing
  the facilities and then assessing them reads TRI once.
- A projector files each facility's results in the workspace keyed by FRS ID (two facilities
  with the same emission rate no longer collide); a later single-tool result still replaces
  the batch one.
- **Tiered screening replaces the top-N cut** (default path): (1) a bound for every
  facility from one unit-rate calculation with the global default stack; (2) facilities at or
  above `screening.hq` (0.1) or `screening.cancer_risk` (1e-6) get their own stacks and an
  own-stack worst case (no weather or Census request: the worst case runs over the SCREEN3
  weather matrix at the most conservative of the screening ambient temperatures); (3) those
  still above, highest risk first, get site weather, residents and the representative case up
  to `max_facilities`; the rest keep their worst case, labelled worst case only. Screened-out
  facilities carry their bound and reason, on the map and in the counts.
- Weather is shared within an ERA5 grid cell, SCC searches once per industry title, EIS
  twin searches run concurrently with their registrations read in bulk, and EIS IDs are reused.
- `[assessment]` settings; step label for the new tool; the inventory and exposure tool
  descriptions point to the batch tool.

## Capabilities

### New Capabilities

- `facility-assessment-tool`: the batch assessment, its stack-source order, selection, caps,
  benchmarks, concurrency and its two views.

### Modified Capabilities

- `app-configuration`: `[assessment]` settings.
- `emissions-inventory-tool`: the inventory is reused for a configured time.
- `assessment-dashboard-state`: batch results attach by FRS ID.

## Impact

- New: `tools/assessment/` (tool, `helpers/steps.py`, `stacks.py`, `chain.py`, `view.py`),
  `config/assessment.py`, `commons/ttl_cache.py`, `api/services/projectors/assessment.py`,
  `tests/conftest.py` (clears the inventory cache per test).
- Changed: `tools/registry.py`, `tools/schemas.py`, `tools/emissions/inventory.py`,
  `tools/exposure/metrics.py` (description), projector ledger/attribution, settings,
  `tools/CLAUDE.md` (the one composition exception).
- The eval cassettes have no recording of the new tool; they must be re-recorded and the
  evals re-run (OpenAI key, costs tokens).
