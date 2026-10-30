## 1. Backend graph

- [x] 1.1 Add `[ui.exposure_graph]` (lanes, node titles, fact labels, quantity labels and units, tier words, reasons, variants) to `settings.toml`, `config/exposure_graph.py` loader, `UiSettings.exposure_graph`, and loader tests including negative ones
- [x] 1.2 Add `api/schemas/exposure_graph.py` (lane, node, edge, quantity, fact) and `Facility.exposure_graph`
- [x] 1.3 Add `api/services/exposure_graph/` (hub, community lane with stacks and age bands, worker lane with both tiers) and attach it in `build_facilities`; `WorkspaceRules.graph` wired in `api/dependencies.py`
- [x] 1.4 Tests: branches, unavailable lane, absent quantity with reason, no computed value, worker tiers
- [x] 1.5 Export the contract and regenerate `frontend/src/types`

## 2. Frontend renderer

- [x] 2.1 Add `@xyflow/react` 12.12.0 and `elkjs` 0.12.0; replace the hand-built lanes, hub, layout and SVG with `layout.ts` (ELK) and a React Flow canvas with custom node and edge components, minimap, controls and fit view
- [x] 2.2 Keep the tab, toolbar (facility, lane isolate), detail panel, focus hook and screen-reader summary, now reading the API graph; format numbers with `lib/format` and digits from the client config
- [x] 2.3 Vitest (jsdom) tests for layout input, formatting of quantities, tab behaviour (empty, lanes, unavailable, detail, Escape, isolate, unknown lane drawn)

## 3. Visual tests

- [x] 3.1 Add `@vitest/browser-playwright` 5.0.5 and `playwright` 1.64.0, a browser-mode Vitest project and `npm run test:visual`
- [x] 3.2 Visual tests: both lanes, missing values, unavailable lane, exceedance, dark, narrow; review every screenshot and keep them as references

## 4. Wiring and docs

- [x] 4.1 Overview third tab and `App.tsx` composition (kept from the previous step), `frontend/CLAUDE.md` and `api/CLAUDE.md` updated

## 5. Verify

- [x] 5.1 `uv run pytest`, ruff format and check, pyright, bandit, function length, `npm --prefix frontend run check`, `npm --prefix frontend run test:visual`
