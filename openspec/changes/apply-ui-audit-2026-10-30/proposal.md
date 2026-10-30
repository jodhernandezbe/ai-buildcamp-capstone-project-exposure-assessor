## Why

The first `/ui-audit` (`docs/ui-audit-2026-10-30.md`) scored every surface of the frontend and
ranked nine improvements. Three are visible on every first load (an empty overview band that
hides the summary cards, a map control bleeding through the Monitoring view, zero counts shown as
data), the rest are small consistency and legibility fixes. All are small; doing them together,
each verified with `/ui-check`, closes the audit instead of leaving a backlog.

## What Changes

- Overview: an empty worst-case section takes its content height so the five summary cards are
  visible at first load, in fullscreen and on narrow screens.
- Layering: the map is its own stacking context so its overlays (basemap button, legend,
  inspector) can never appear above the Monitoring view or any other covering layer.
- Map legend: before any facility is mapped, one line ("No facilities mapped yet") replaces the
  four zero counts; counts appear once pins exist.
- Monitoring sessions table: secondary columns (model calls, tool calls, tokens, duration) hide
  under a narrow container and the table fits the pane; every header is distinct.
- Settings drawer: each collapsed section shows the state of its keys in words ("Key saved",
  "Key missing") so the drawer is informative before anything is opened.
- Rail: disabled actions carry their reason as an accessible description as well as a tooltip.
- Chat welcome: the compartment badges ("AIR • WATER • SOIL") become sentence-case words with the
  planned ones marked as such, following `DESIGN.md`.
- Exposure chain: edge value labels move to the documented micro-badge size (11 px label,
  12 px value); references re-approved after looking.
- Demographics card: age bands the API did not send are omitted from the bar and listed as "not
  reported" instead of rendering as 0 %.
- `frontend/DESIGN.md` gains the four rules the audit consolidated (empty sections take content
  height; layering ladder; counts only when items exist; disabled controls say why).

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `web-ui-shell`: ADDED requirements for empty-section height, layering ladder, legend before
  data, disabled-control reasons, compartment badges wording, age-band absence.
- `monitoring-dashboard`: ADDED requirement for the sessions table fitting its pane.
- `exposure-chain`: ADDED requirement for the minimum size of edge value labels.

## Impact

- `frontend/src`: `features/overview/{EpaOverviewRibbon,DemographicsCard}.tsx`,
  `features/map/{MapLegend,ExposureMapCanvas}.tsx`, `features/monitoring/SessionsTable.tsx`,
  `features/settings/SettingsDrawer.tsx`, `components/ui/{Accordion,BrandLogo}.tsx`,
  `components/layout/LeftNavRail.tsx`, `features/exposure-chain/FlowEdge.tsx`, their tests, the
  exposure-chain screenshot references, `frontend/DESIGN.md`.
- No API, agent or Python change; no new dependency.
