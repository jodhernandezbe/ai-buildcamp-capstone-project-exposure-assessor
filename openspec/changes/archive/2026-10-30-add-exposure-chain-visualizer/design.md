## Context

- The Overview (`features/overview/OverviewPanel.tsx`) shows a Summary ribbon and a Risk-by-group
  view of one `WorkspaceState`. The chat's chosen facility is `workspace.selected_frs_id`; the map's
  pinned facility is local state inside `FacilityInspector`, so nothing else can see it.
- `Facility` already carries `conditions_of_use`, `lifecycle_stages`, `naics_subsector(_title)`,
  `operating_hours_per_year`, `emission_rate_g_s`, `total_release`, `exposure` (with `dose` by age
  band), `receptors` and `screening`. `add-occupational-risk-assessment` adds `occupational_exposure`
  and `operational_profile` (TWA, benchmark and source, limit ratio, tier, schedule, CDR sector).
- `frontend/CLAUDE.md`: feature folders with one-way imports (`components/` -> `features/` -> `App.tsx`,
  features never import each other's internals), tokens not literal colours, only API values, no
  computing in the browser, display settings from the client config, Vitest beside pure helpers.
- The supplied draft is a single component with literal Tailwind slate/cyan colours, hard-coded
  values (0.74, "10 m³/shift", "ChemSTEER ..."), a status prop of its own (`acceptable`/`elevated`/
  `exceedance`), `animate-in` (no such plugin here) and an inspector sentence claiming sync with
  "EcoFate backend agents". It is a good layout reference, not a drop-in.

## Goals / Non-Goals

**Goals:**
- A readable, interactive picture of the worst-case chain per pathway, with the quantity on every link.
- A pathway is data: adding one never edits the diagram.
- Native look (tokens, glass, light/dark, reduced motion), keyboard and screen-reader usable.

**Non-Goals:**
- No backend, schema or new dependency; no new scientific value; no graph editor, zoom or drag.
- No change to Summary, Risk by group, the map or the chat beyond the tab and the one callback.

## Decisions

**1. Tab, not card.** `OverviewPanel` gets a third `View` ("chain"). `App.tsx` builds `<ExposureChainTab/>`
and passes it as the `chain` slot (features may not import each other). The tab stays mounted and is
`hidden` when inactive (like the ribbon), so its selection survives tab switches.

**2. Plain SVG diagram, fixed coordinates.** Layout is computed from the lane count: columns
(hub, pathway, route, receptor, endpoint) and one row per lane, the hub centred. Edges are cubic `<path>`s;
nodes are `foreignObject` buttons (HTML text wraps, tokens apply, focus and ARIA are native); edge labels
are small pills at the midpoint. The SVG has a minimum width and its wrapper scrolls horizontally. A
graph library (React Flow, D3) is not added: the graph is tiny, fixed in shape, and read-only.

**3. Lane registry (the extension point).**
```
features/exposure-chain/
  model.ts          Value, ChainField, NodeReading, LaneSpec, DiagramNode, DiagramEdge, Diagram
  values.ts         "not reported + reason" formatting helpers (API values only)
  lanes/community.ts, lanes/worker.ts, lanes/index.ts   <- LANES registry (one line per lane)
  hub.ts            the facility hub reading (name, chemical, NAICS, condition of use, stage)
  build.ts          buildDiagram(facility, workspace, options) -> Diagram (pure)
  layout.ts         pure geometry: node boxes, edge paths, label positions from lane count
  focus.ts / useFocusedFacility.ts   which facility is shown
  ExposureChainTab.tsx   toolbar (facility picker, lane isolate, ventilation tier), diagram, detail
  DiagramCanvas.tsx, DiagramNode.tsx, DiagramEdge.tsx, DetailPanel.tsx, nodeIcons.ts
```
A `LaneSpec` is `{ id, label, available(facility), release(ctx), nodes: [pathway, route, receptor,
endpoint] (NodeSpec), links: [route-in, receptor-in, endpoint-in] readers }`; every reader is pure, takes
only API data and returns a `Value`/`NodeReading`. A dermal or consumer lane is one file.

**4. Worst case.** The community lane reads `exposure.*_worst.high` and the stack named by `high_stack`
(`worst_case.distance_m`, `max_concentration_ug_m3`), the dose by band (`exposure.dose`) and the
receptors; the worker lane reads `occupational_exposure.worst_case` (or `baseline` when chosen). The
default facility is the assessment's `selected_frs_id` (the highest risk). Nothing is ranked or combined
in the browser.

**5. Status.** Reuses `Status`/`StatusPill`; the occupational tier is relabelled by a closed lookup
(`acceptable -> below`, `elevated -> near`, `exceedance -> above`) with the tier's word as the pill label.
Edge strokes use the lane endpoint's status token, so a lane that exceeds reads as such along its length.

**6. Interaction state** lives in the tab: `selectedNode`, `hoverNode`, `isolatedLane`, `tier`. The
lane of the hovered/focused/selected node is prominent, others get reduced opacity (not hidden).
Escape closes the detail with `preventDefault()` + `stopPropagation()`. Flow animation is a CSS
`stroke-dashoffset` keyframe disabled under `motion-reduce`.

**7. Focus.** `resolveFocus(facilities, selected, pinned)` as before; `useFocusedFacility` drops the pin for
good when the selection or workspace epoch changes. The tab's facility picker calls the same `onPin`.

**8. Accessibility.** Nodes are buttons named "Step N of 5, lane: label, value"; edges are `<g>`s with a
`<title>`/`aria-label` and also listed in a visually hidden `<ol>` summary of each lane; the detail panel
is a labelled region; colour is never the only cue.

**9. Tests.** Pure: `build.test.ts` (both lanes full/empty/non-finite, tier choice), `layout.test.ts`
(positions for 1, 2 and 3 lanes), `lanes/index.test.ts` (unique ids, four nodes, total readers),
`focus.test.ts`. RTL: tab empty state, both lanes drawn with connection labels, unavailable lane,
hover highlight, detail incl. age-band doses, Escape, lane isolate, tier switch, reduced motion, no
hard-coded value, OverviewPanel third tab keeps state.

## Risks / Trade-offs

- **Fixed-geometry SVG** does not reflow; mitigated by horizontal scroll and a minimum width.
- **foreignObject** is not exportable to image tools; acceptable for an on-screen view.
- **Sibling dependency:** the worker lane needs `add-occupational-risk-assessment` data; without it the lane
  is drawn empty with its reason.
- **Closed icon map** needs one line per new icon.
