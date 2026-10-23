## Why

The Overview panel's Results table repeats what the rest of the dashboard already says: the map
has every facility with a hover card (and a click to pin it) for the per-facility details, and
the new risk-by-group charts show where the risk sits. The table costs a large block of panel
height, and its only unique job, jumping from a row to the facility on the map, is a second way
to do what clicking a marker already does. The map should be the way to see a facility.

## What Changes

- Remove the Results table from the Overview panel: the component, its row/sort/fold helpers and
  their tests.
- Remove the click-to-focus path that only the table used: the `focusFacility` request and
  `FacilityFocus` in the workspace store, the `focus` props of `MapPanel`, `ExposureMapCanvas`
  and `FacilityInspector`, the map's "frame this facility" effect and its zoom setting, the
  `onFocusFacility` prop of the Overview panel, and their tests.
- Keep what the risk charts need from the old helpers (whether a facility was assessed or
  screened out), in a small module of its own.
- Specify the click-to-pin behavior of the facility card (the way to see details after this
  change), which the code and tests already have but the spec did not state.
- Reword the chart requirements so they no longer refer to the table.
- **BREAKING (UI only):** the per-facility list with screening outcomes, screened-out values and
  the folded group of unassessed facilities is gone. A facility with no coordinates is no longer
  visible anywhere in the dashboard.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `web-ui-shell`: removes "Results table in the Overview panel"; rewords "Risk by industry,
  condition of use and life cycle stage" and "Expandable chart sections" without the table;
  adds the click-to-pin scenarios to "Facility inspector popover".

## Impact

- Frontend only: `features/overview/` (`ResultsTable.tsx`, `resultsRows.ts` and their tests are
  deleted; `OverviewPanel.tsx`, `riskGroups.ts`, `RiskGroupSection.tsx` change), `features/map/`
  (`MapPanel.tsx`, `ExposureMapCanvas.tsx`, `FacilityInspector.tsx` and its test),
  `hooks/useWorkspaceStore.ts`, `App.tsx`.
- No API, backend, contract or data change; no dependency change.
- The assistant's chat report can still contain a results table (that is the agent's prose, a
  different thing); nothing in the prompt or tools changes.
