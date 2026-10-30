## 1. First-load impression (audit proposals 1, 2, 5)

- [x] 1.1 `EpaOverviewRibbon`: first grid row `auto` when there are no scenario drivers; test that the empty worst-case section does not stretch and the cards follow
- [x] 1.2 `ExposureMapCanvas`: `isolate` on the map root; test that the root carries the isolation class
- [x] 1.3 `MapLegend`: "No facilities mapped yet" and no counts while empty; counts once facilities exist; tests for both

## 2. Monitoring and settings (proposals 3, 4)

- [x] 2.1 `SessionsTable`: container query hides secondary columns when narrow; table fits the pane; test the column classes
- [x] 2.2 `AccordionSection` optional `summary`; `SettingsDrawer` shows key state per section; tests

## 3. Consistency and legibility (proposals 6, 7, 8, 9)

- [x] 3.1 `LeftNavRail` `Item`: `aria-description` with the blocked reason; test
- [x] 3.2 `BrandLogo` compartment pill in words ("Air", "Water (planned)", "Soil (planned)"); test
- [x] 3.3 `FlowEdge` labels 11 px / 12 px; re-run `test:visual`, look at every changed chain image, approve
- [x] 3.4 `DemographicsCard`: omit absent bands, list them as not reported; test

## 4. Design document and verification

- [x] 4.1 `frontend/DESIGN.md`: empty sections take content height; layering ladder; counts only when items exist; disabled controls say why
- [x] 4.2 `/ui-check` on the overview (first load), map legend, monitoring table, settings drawer, welcome and exposure chain; record the tables in `verification.md`
- [x] 4.3 `npm --prefix frontend run check`, `test:visual`, pre-commit on the changed files pass
