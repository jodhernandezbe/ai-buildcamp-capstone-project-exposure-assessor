## Context

Code that exists today (read before planning):

- `OverviewPanel` renders the ribbon, the three `RiskGroupSection`s and `ResultsTable`, wrapping
  the ribbon and the table in `contents`/`hidden` divs so an expanded chart can hide them while
  they stay mounted. Its `onFocusFacility` prop is wired from `App` to `store.focusFacility`.
- `useWorkspaceStore` keeps `focus: FacilityFocus | null` (`{frsId, nonce}`) and
  `focusFacility`; `App` passes `focus` to `MapPanel`, which passes it to `ExposureMapCanvas`
  (an effect fits the map to that facility at `FOCUS_MAX_ZOOM`) and to `FacilityInspector` (an
  effect pins that facility's card).
- Pinning by click is separate and already works in `FacilityInspector` (tests under "pinned card"
  cover click-to-pin, closing by control, Escape and map click, and hover not replacing a pinned
  card), but `web-ui-shell` only specifies hover and keyboard focus.
- `resultsRows.ts` holds the table's row model (`toRow`, `OUTCOME_LABEL`, sort and fold helpers)
  and also `Outcome`/`isAssessed`, which `riskGroups.ts` and `RiskGroupSection.tsx` import.

## Goals / Non-Goals

**Goals:** delete the table and everything only it used, leave the map's hover and click-to-pin
exactly as they are, keep the risk charts working.

**Non-Goals:** a replacement list of facilities, a way to reach facilities without coordinates,
clicking a chart bar to focus a facility (a possible later use of the focus path, deliberately not
kept now), or any backend change.

## Decisions

1. **Delete, do not hide.** `ResultsTable.tsx`, `ResultsTable.test.tsx`, `resultsRows.ts` and
   `resultsRows.test.ts` are removed. Nothing stays behind a flag.

2. **Move only what the charts need.** The charts need to know whether a facility was assessed
   (it has a worst-case result: outcome `full` or `worst_case_only`) or screened out. That
   becomes `features/overview/assessment.ts` with `Outcome`, `outcomeOf(facility)` and
   `isAssessed(facility)`, taking the `Facility` directly (the row indirection `toRow` existed
   for the table, so it is dropped; the user asked to keep `toRow`/`isAssessed`'s job, which is
   kept in this smaller form). `riskGroups.ts` and `RiskGroupSection.tsx` import it; its own small
   test covers every outcome. `OUTCOME_LABEL` and the sort/fold helpers go with the table.

3. **Remove the focus path end to end.** Delete `FacilityFocus`, `focus`, `focusFacility` from the
   store (and the now unused `useCallback` for it); `focus` from `App`, `MapPanel`,
   `ExposureMapCanvas` and `FacilityInspector`; the canvas effect and the `FOCUS_MAX_ZOOM`
   constant; the inspector effect that pins on a new focus; and `onFocusFacility` from
   `OverviewPanel`. Hover, keyboard focus and click-to-pin in `FacilityInspector` are not touched.
   The `FacilityInspector.test.tsx` describe "focus from the results table" is deleted; its
   pinned-card tests stay and are the proof that click-to-pin still works.

4. **Overview layout.** Without the table the panel is the ribbon and the three chart sections.
   Expanding a section still hides the ribbon and the other sections (wrapper `hidden` +
   `contents` stays for the ribbon). The charts' grid keeps `mt-3`; with nothing below it, the
   panel's bottom padding is enough. `OverviewPanel.test.tsx` loses the table assertions (the
   "Results" region checks become checks that the ribbon is hidden while expanded).

5. **Specs.** `web-ui-shell`: REMOVED "Results table in the Overview panel" (reason and
   migration given); MODIFIED "Risk by industry, condition of use and life cycle stage" ("Below
   the summary ribbon"), "Expandable chart sections" (the ribbon and other sections are hidden),
   and "Facility inspector popover" (two new scenarios: a click pins the card; a pinned card is
   not replaced by hovering), documenting behavior the code already has.

6. **No migration of data or API.** Nothing in the backend referenced the table. `api/CLAUDE.md`
   and `frontend/CLAUDE.md` do not mention it (checked), so no rule file changes.

## Risks / Trade-offs

- **Lost information.** The table was the only place listing every facility with its screening
  outcome, the value a screened-out facility was left out on, and the folded unassessed group;
  the charts count screened-out and assessed facilities per group but show no per-facility
  outcome. Accepted by the user.
- **Facilities without coordinates** appear on neither the map nor any list now. The map already
  omits them (a counted warning in the inventory); the dashboard gains no new gap but loses the
  table, where they were visible. Noted, not addressed.
- **Dead-code risk the other way:** removing the focus path means a later "click a bar to show the
  facility" feature must rebuild it; kept out on purpose so no unused code remains.
- **Test coverage:** the deleted tests covered the table's sort, fold and row click only; the
  retained ones (risk groups, panel, inspector pin tests) cover everything that stays.

## Open Questions

None.
