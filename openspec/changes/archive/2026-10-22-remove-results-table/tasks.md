## 1. Keep what the charts need

- [x] 1.1 Add `frontend/src/features/overview/assessment.ts` (`Outcome`, `outcomeOf`, `isAssessed` on a `Facility`) with `assessment.test.ts` covering full, worst case only, both screened-out outcomes and not assessed
- [x] 1.2 Switch `riskGroups.ts` and `RiskGroupSection.tsx` to it (no `toRow`/`ResultRow`); keep every existing `riskGroups.test.ts` and `OverviewPanel.test.tsx` expectation about assessed and screened-out counts passing

## 2. Remove the table

- [x] 2.1 Delete `ResultsTable.tsx`, `ResultsTable.test.tsx`, `resultsRows.ts` and `resultsRows.test.ts`; remove the table and its wrapper from `OverviewPanel.tsx`; update `OverviewPanel.test.tsx` (no "Results" region; expanding a section still hides the ribbon and the other sections, all stay mounted)

## 3. Remove the click-to-focus path

- [x] 3.1 Remove `FacilityFocus`, `focus` and `focusFacility` from `useWorkspaceStore.ts`, and the `focus`/`onFocusFacility` props from `App.tsx`, `OverviewPanel.tsx`, `MapPanel.tsx`, `ExposureMapCanvas.tsx` (including its frame-this-facility effect and `FOCUS_MAX_ZOOM`) and `FacilityInspector.tsx` (including its pin-on-focus effect)
- [x] 3.2 Delete the "focus from the results table" tests in `FacilityInspector.test.tsx`; confirm the pinned-card tests (click pins, closes by control, Escape and map click, hover does not replace a pinned card) and the marker/keyboard tests still pass unchanged

## 4. Verification

- [x] 4.1 Run `npm --prefix frontend run check` and `npm --prefix frontend run build`; search the frontend for leftovers (`ResultsTable`, `resultsRows`, `focusFacility`, `FacilityFocus`, `FOCUS_MAX_ZOOM`, `onFocusFacility`) and confirm none remain
- [ ] 4.2 Look at the panel in a real render (headless Chrome with synthetic data, as before): ribbon, three charts, nothing below them, an expanded section, and a marker card pinned by click on the map
- [x] 4.3 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check and `uv run pre-commit run --all-files`
