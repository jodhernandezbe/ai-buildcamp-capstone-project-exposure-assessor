## Context

`tools/assessment` screens in tiers. Tier 1 computes one unit-rate bound with the global default
stack and scales it per facility; a facility below both thresholds is screened out. Tier 2
(`screen` in `helpers/tiers.py`) keeps the candidates sorted by emission rate (= largest bound
first) and cuts them at `max_refined`; the cut ones become `NotAssessed` entries in
`Findings.skipped`, which the model's view lists but `_artifact` does not return. The API places
every inventory facility on the map and attaches batch results by FRS ID, so a cut facility has no
`screening`; the card's `noStacks` then says "Not assessed yet: no stack parameters were obtained".
`choose_stacks` never returns empty: NEI, else PSTK, else the global default.

## What I measured (live benzene, 844 facilities)

- **Refining all of them is cheap in compute.** `refine_all` with the generic stack (the pure
  SCREEN3 worst case over the four screening temperatures), four workers: 100 facilities 0.6 s,
  400 2.5 s, 844 5.3 s. With up to three PSTK stacks per facility expect up to about three times
  that.
- **What the facility count does cost is lookups:**
  - 47 distinct industry titles, so 47 SCC searches however many facilities (made once per title).
  - Every facility has its industry title from the inventory (0 missing), so no per-facility TRI
    industry request.
  - EIS IDs: only 20 of 844 had them from the inventory listing. The own registrations are
    already bulk (`registry_id/in/...`, 100 IDs per request). The **same-site (twin) search is not**:
    one request per facility, each about 4.3 to 4.8 s, four at a time, so about 15 minutes for
    ~820 facilities. A direct attempt to time the whole lookup did not finish in 10 minutes. This,
    not the refinement, is what `max_refined` was protecting.
- **The FRS service does take a list of names**: `primary_name/in/a,b` answered in one request
  (2 names, 4 rows, 4.5 s). Two limits found: a name containing a comma cannot be sent in a list
  (the comma is the separator; 1 of 844 names had one), and a batch of 40 names failed with
  "The query could not be parsed" (some name has a character the query parser rejects).

## Goals / Non-Goals

**Goals:** every facility refined (fallback included) with no ranking cut; unassessed facilities,
when there are any, reported with their real reason in the program's data and on the card; the EIS
twin search no longer the bottleneck.

**Non-Goals:** raising `max_facilities` (the weather and Census request cost is real); changing
the thresholds; changing which source a stack comes from; the model's text view beyond what the
spec lists.

## Decisions

1. **No ranking cut at tier 2.** `screen` returns every candidate and no `over`. `max_refined` is
   kept as a safety bound with a high default (5,000, above any chemical in the TRI window of
   `max_pages * page_size`): candidates beyond it are returned as `NotAssessed` with the reason
   "more than {bound} facilities reach a threshold; refining them all was not attempted", and the
   result's warnings say so, so a limit is never silent. Its comment in `settings.toml` is rewritten
   to say it is a safety bound, not a selection.

2. **By-ID path.** `_by_id` refines every facility asked for that is in the inventory and gives
   the full chain to the first `max_facilities` (in the order given), keeping the others at worst
   case only (`worst_case_only`), instead of listing them as not assessed. FRS IDs not in the
   inventory are still listed as not assessed (they have no record to place).

3. **Artifact.** `AssessmentArtifact` gains `not_assessed: list[NotAssessed]` (the same
   `{frs_id, reason}` the model's view lists). `_artifact` fills it from `Findings.skipped`.

4. **Projection.** `api/services/projectors/assessment.py` files each not-assessed facility as
   `Screening(outcome="not_assessed", reason=...)` for facilities the inventory placed (FRS IDs
   with no record are ignored; there is nothing to place). `ScreeningOutcome` gains
   `"not_assessed"`. The facility status stays absent (marker "Not computed"). A not-assessed
   reason never overwrites a real result for the same FRS ID.

5. **Card text.** `noStacks` says: screened out on the bound: the existing sentence; outcome
   `not_assessed`: "Not assessed: {reason}"; no screening at all (the batch never covered the
   facility): "Not assessed yet: the batch assessment has not covered this facility." The old
   sentence "no stack parameters were obtained" goes away, since a fallback stack always exists.
   `features/overview/assessment.ts` accepts the new outcome (not assessed; not an assessed one,
   not screened out).

6. **Bulk twin search (`eis.py`).** `[frs_eis].twins_path` becomes a list path
   (`primary_name/in/{names}/state_code/equals/{state}`, checked live to answer the same as the
   per-name query); a new `twin_batch_size` (default 20) sets names per request.
   `_twins_of` groups the facilities' names (deduplicated) by state, splits into batches, runs
   `twin_workers` batches at a time, and filters each response rows locally by exact name, state
   and distance, exactly as the per-facility search did. The service's parser accepts only
   letters, digits, space, "-" and "." (measured: `& \' ( ) / # ; : " + =` and the comma fail
   alone or in a list, each failure costing the client's three attempts), so a name outside
   `twin_list_pattern` is not searched (measured on benzene: 46 failed requests, about half the
   time of the first version); one name alone uses the `equals` path. A batch the service rejects
   with a query error is split in halves and retried down to a single name; a single name that is
   still rejected leaves that facility without a twin and with the existing note (never an
   exception). The same-site results are still reused for `cache_seconds`. Measured on live benzene (844
   facilities, 819 without an own registration): 347 s with the first version, 179 s once
   unparseable names are skipped, against more than 10 min before; 437 facilities got EIS IDs
   (same as before). A few remaining batch rejections (names with "." before a comma or "ST.")
   are bisected.

7. **Config.** `[assessment].max_refined = 5000` (safety bound, comment rewritten);
   `[frs_eis].twins_path` and `twin_batch_size`; validated on load with tests (positive batch
   size, the path must contain `{names}`).

8. **Tests.** Tiers: no candidate is dropped below the bound; the safety bound returns the rest as
   not assessed and warns; by-ID beyond the cap keeps worst-case only. Artifact has
   `not_assessed`. Projector: a not-assessed facility gets the outcome and reason, a facility with
   a real result is never overwritten, an unknown FRS ID is ignored. EIS: batches of names, local
   filtering by name/state/distance as before, comma names individually, bisect on a rejected
   batch, one request per batch not per facility. Card: each of the three texts. Spec: validate.

## Risks / Trade-offs

- **Wall-clock for large chemicals.** Refining everything is more work than before; compute stays
  seconds, the EIS and SCC lookups scale with distinct names and titles, and the safety bound caps
  the pathological case. A first real run on benzene is part of the verification.
- **FRS parse failures.** The service rejects some batches; bisecting costs extra requests in the
  worst case (each rejected batch of 20 can cost up to about 40 more small requests) but only for
  the affected names. The previous behavior (one request per facility) is the floor.
- **More markers get colour,** which changes how the map looks for big chemicals (more red or
  green markers where there were grey ones). That is the intended effect.
- **Model text unchanged.** The model still reads counts and the not-assessed list; the card is
  where the reason is shown.

## Open Questions

- Is 5,000 the right safety bound? It is above what the TRI window can return for any single
  chemical today (40 pages of 1,000 rows), so in practice it never triggers; it exists so that a
  future change in `max_pages` cannot silently drop facilities.
