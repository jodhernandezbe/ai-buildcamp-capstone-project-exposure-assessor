# /ui-check of the audit fixes, 2026-10-30

Rendered two ways. Screenshot tests (`test:visual`, Playwright Chromium, light and dark) for the
overview ribbon and the exposure chain; references regenerated and every new image looked at.
Live app (built frontend, `uv run python -m api`, Playwright from the frontend package) for the
shell, legend, settings, welcome and Monitoring, in light and dark at 1440 × 900 and 720 × 900,
plus a measured overflow check of the sessions table at 1280, 1440 and 1920 px.

| Surface and check | Light | Dark | Evidence |
| --- | --- | --- | --- |
| Overview first load: cards follow the one-line worst-case note | pass | pass | `ribbon-empty-*`, `ribbon-ready-*` references; live first load and narrow stack |
| Map overlays stay inside the map | pass | pass | Live Monitoring view: no basemap control over the table (it showed before) |
| Legend before data: sentence, no counts | pass | pass | Live first load: "No facilities mapped yet."; unit test with facilities keeps counts |
| Sessions table fits its pane | pass | pass | Measured: no overflow at 1280, 1440, 1920 px; four, four and six columns visible |
| Settings sections say their key state | pass | n/a | Live drawer: "Key saved", "2 of 2 keys saved"; unit tests for missing and unknown |
| Disabled rail actions describe why | pass | pass | Unit test on `aria-description`; tooltip unchanged |
| Compartment badges in words | pass | pass | Live welcome: "Air", "Water (planned)", "Soil (planned)" |
| Edge labels at 11 px / 12 px | pass | pass | Regenerated chain references, ten images looked at |
| Absent age band not drawn as 0 % | pass | n/a | Unit test: bar lists reported bands, "Not reported: ages 5-17, 65+" |
| Tokens only, no literal values | pass | pass | Static grep of changed files |
| Design document test | pass | | Tokens unchanged |
| Contrast test | pass | pass | Unchanged tokens |
| Screenshot suite | pass | pass | 16 of 16 |

Result: verified. No `fail` rows.

Findings during the check:

- The first sessions-table fix (hide columns under one breakpoint) passed its unit tests but
  still overflowed when measured live. Replaced with a fixed layout and two tiers; the design
  and spec record the change.
- `test:visual` passed after the edge-label change even though the labels grew: the 1 % pixel
  tolerance absorbs small text changes, and `-u` only rewrites failing references. The chain
  references were deleted and regenerated so they show the current labels. Small text changes
  need a deliberate regeneration; worth a note in the kit's verify loop.
