## Why

The Overview shows risk numbers but not how they arise. A reader cannot see, for the facility with the
worst result, which release feeds which pathway, by which route, to which people, and what each link
carries. An interactive diagram of those worst-case connections, in a tab beside Summary and Risk by
group, makes the story explorable, and must take new pathways later without rewriting the diagram.

## What Changes

- **New Overview tab "Exposure chain"** beside Summary and Risk by group. It draws one interactive
  diagram for one facility (default: the facility the assessment selected as the worst case): a facility
  hub on the left fans out into **lanes**, one per worst-case pathway, each running
  source → pathway → route → receptor → endpoint.
  - Community lane: stack release → outdoor air (peak concentration, distance, weather) → inhalation →
    residents by age band (dose per band) → worst-case hazard quotient and cancer risk.
  - Worker lane: fugitive release → indoor workplace air (box model: ventilation, mixing, concentration)
    → inhalation → shift worker (schedule) → 8-hour average against the occupational limit, hazard
    quotient, cancer risk and tier. Worst-case or baseline ventilation can be chosen.
- **Every connection is labelled** with the quantity it carries (release rate, concentration, dose, ratio),
  read from the API; nodes show their headline value and status in words and colour.
- **Interaction:** hover or focus a node to highlight its lane; click or Enter to open a detail panel
  (fields with units, sources, assumptions, warnings, and a by-age-band dose list for the receptors);
  pick the facility; isolate one lane; direction-of-flow animation (off for reduced motion).
- **The server builds the graph.** Each facility in the workspace carries an `exposure_graph` (lanes,
  nodes, edges; every quantity with its value, unit, source or reason), projected from the validated
  facility by `api/services/exposure_graph/`; its fixed text and units live in `[ui.exposure_graph]`.
  The browser only lays it out and draws it, so chat, report and UI share one source, and a new pathway
  is a backend projector, not a frontend edit.
- **Branching graph.** Every evaluated stack is its own source node feeding the outdoor air, and every
  resident age band is its own receptor node with its dose; the worker lane carries the worst-case and
  baseline ventilation values. Layout is automatic (ELK.js) and the canvas (React Flow) pans, zooms,
  fits the view and has a minimap.
- **Visual tests.** Browser-mode Vitest (Playwright Chromium) renders each state, light and dark, wide
  and narrow, saves screenshots and compares them on later runs.
- **Focus.** A map pin selects the facility; so does the chat's selection and the tab's own picker.
- **Replaces the first attempt** (a row of five cards inside Summary): removed, not kept.

## Capabilities

### New Capabilities
- `exposure-chain`: the interactive worst-case exposure diagram, its lane registry, connection labels,
  detail panel, focus rules and accessibility.

### Modified Capabilities
- `web-ui-shell`: the Overview gains the third tab, and pinning a facility on the map focuses it.
- `assessment-dashboard-state`: each facility carries its exposure graph.

## Impact

- Backend: `api/schemas/exposure_graph.py`, `api/schemas/workspace.py` (`Facility.exposure_graph`),
  `api/services/exposure_graph/`, `api/services/projectors/{facilities,rules}.py`, `api/dependencies.py`,
  `config/exposure_graph.py`, `config/ui.py`, `config/settings.toml`; generated contract and types.
- Frontend: `frontend/src/features/exposure-chain/` (renderer only), Overview third tab, map `onPin`, `App.tsx`.
- New dependencies: `@xyflow/react` 12.12.0, `elkjs` 0.12.0; dev: `@vitest/browser-playwright` 5.0.5,
  `playwright` 1.64.0 (Chromium for visual tests). Storybook is not added: the browser-mode tests render
  every state from fixtures, which is the review surface Storybook would give, with one less toolchain.
- Reads `occupational_exposure` and `operational_profile` from `add-occupational-risk-assessment`.
- The user asked for the Overview to change, so the default of leaving Overview/Map/Chat alone is lifted
  for the tab and the one callback only.
