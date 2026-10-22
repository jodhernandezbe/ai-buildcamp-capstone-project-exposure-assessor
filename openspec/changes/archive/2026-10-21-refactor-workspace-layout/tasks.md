## 1. Backend configuration and thread retention

- [x] 1.1 Add `[ui.layout]` (rail collapsed/default/min/max px, chat default share, min px, max share, overview default/min/max share) and `[ui.threads] max_retained` to `config/settings.toml`, each with a comment on its basis
- [x] 1.2 Add frozen dataclasses and validation to `config/ui.py` (min ≤ default ≤ max, shares in (0,1), positive ints, no bools); negative tests in `tests/config/` naming the offending key
- [x] 1.3 Add `LayoutConfig` to `api/schemas/settings.py` and expose it in `ClientConfig` via the settings router; test the endpoint returns the layout values
- [x] 1.4 Make `ThreadStore` track least-recently-used order (touched by `claim` and snapshot) and evict the oldest idle thread when over `max_retained`, never a running one; tests for limit, eviction order and all-running
- [x] 1.5 Add `ThreadStore.snapshot` returning text-only user/assistant messages (no tool calls/results), the workspace (empty state if none) and usage; check that guardrail pivots appear in the history and include them if the graph does not store them as assistant messages

## 2. Thread snapshot endpoint and contract

- [x] 2.1 Add `ThreadSnapshot` (and message model) to `api/schemas/chat.py`, reusing `WorkspaceState` and the usage totals
- [x] 2.2 Add `GET /api/v1/chat/threads/{thread_id}` to `api/routers/v1_chat.py` as a thin handler: 200 snapshot, 404 generic unknown, 422 malformed id; no key, exception text or headers in any response
- [x] 2.3 Tests in `tests/api/`: held thread, unknown thread, mid-turn snapshot, malformed id, leak-free body
- [x] 2.4 Run `uv run python -m scripts.export_contract` and `npm --prefix frontend run gen:types`; confirm `check:contract` passes

## 3. Frontend dependencies and primitives

- [x] 3.1 Add `react-resizable-panels` and `remark-gfm` at exact pinned versions (`npm --prefix frontend`), update the lockfile, run `npm audit`
- [x] 3.2 Add a `ResizeObserver` stub to `src/test/setup.ts` and `resize` to `src/test/fakeMaplibre.ts`
- [x] 3.3 Add `getThread` and the snapshot type re-export to `services/apiClient.ts` and `types/workspace.ts`; extend `useClientConfig` types for layout
- [x] 3.4 Extract `useFocusTrap` from `ModalSheet` into `components/ui/` with tests (Tab wrap, Escape, focus return)
- [x] 3.5 Add `components/ui/` primitives with tests: `Accordion`, `InfoTooltip`, `Banner`, `BottomDrawer` (resize, maximize, Esc, focus trap)
- [x] 3.6 Add `PanelSplitter` (1 px line, 3 px accent on hover/focus/drag, resize cursor, separator role) and a pure `limitsToPercent` helper that converts px/share limits to panel percentages, with unit tests including restored-size clamping

## 4. Workspace shell, panels and fullscreen

- [x] 4.1 Rewrite `SplitWorkspace` with nested `react-resizable-panels` groups (rail | analysis | chat, and overview / map inside analysis), sizes from layout config, sizes-only `autoSaveId` persistence behind try/catch
- [x] 4.2 Add `PanelHeader` with title and a `Maximize2`/`Minimize2` toggle ("Enter fullscreen" / "Exit fullscreen"); split `OverviewPane` into `OverviewPanel` and `MapPanel` using it
- [x] 4.3 Implement fullscreen by hiding the other regions with CSS (nothing unmounted, hidden regions `aria-hidden`/`inert`), restore previous sizes on exit
- [x] 4.4 Implement the single `Esc` handler that skips events already handled by the inspector or drawer (`defaultPrevented`); make the inspector and drawer call `preventDefault` when they close
- [x] 4.5 Keep the narrow-viewport fallback: rail forced to icons, segmented Overview/Copilot, no splitters, both panes mounted
- [x] 4.6 Tests: all splitters have separator roles and keyboard steps, chat stops at max share, fullscreen toggle and Esc, map instance survives fullscreen, no page scroll classes, layering test still passes

## 5. Chat dock collapse and tables

- [x] 5.1 Make the chat panel collapsible with a header collapse button and a right-edge restore tab; remove the gear from `TopHeaderBar` and its `onOpenSettings` prop
- [x] 5.2 Test collapse during a streaming turn keeps the stream and the composer draft, and restore returns the previous width
- [x] 5.3 Enable `remark-gfm` in `MessageStream` (raw HTML stays off) and render tables inside a horizontal scroll container with token-based shaded header, zebra rows, 1 px dividers, `tabular-nums` and no cell wrapping; add `min-w-0` so the message cannot widen the dock
- [x] 5.4 Tests: pipe table renders `<table>/<thead>/<tbody>`, wide table sits in an `overflow-x-auto` wrapper, `<script>` still shown as text, existing message tests pass

## 6. Map behavior

- [x] 6.1 Add a `ResizeObserver` (rAF-coalesced, disconnected on cleanup) in `ExposureMapCanvas` that calls `map.resize()`; test that a size change calls `resize` and that cleanup disconnects
- [x] 6.2 Add the map toolbar with "Reset to USA view" (`fitBounds` of the configured `initial_view`, same padding, jumps under reduced motion); test it and that markers stay
- [x] 6.3 Render the Map panel shell at once and put the loading state inside it; confirm the first frame after config is the US view with no facilities
- [x] 6.4 Confirm facility framing still flies only on a new `framing_version`, and that the legend padding still applies in the resized panel

## 7. Navigation rail and run history

- [x] 7.1 Build `components/layout/LeftNavRail.tsx` as a controlled component (brand, toggle, "New analysis", Workspace entry, run list, Settings at the bottom); collapsed = icons with accessible names and tooltips; `aria-current` on the active run
- [x] 7.2 Wire the rail to a collapsible panel (configured collapsed width, 200–320 px expanded range) with the toggle and sash
- [x] 7.3 Add `hooks/useRunHistory.ts` (React state only, newest first, title from first user message) and change `useAgentStream` to run on the active thread, with `newRun` (no `DELETE`) and `selectRun`
- [x] 7.4 Add a `restore` action to `chatState` and apply the snapshot's messages, workspace (re-frames the map) and usage on `selectRun`; block switching while busy
- [x] 7.5 Handle 404 on select: show "no longer available", drop the run, keep the current conversation
- [x] 7.6 Tests: new run keeps the old one listed, select restores, busy blocks switching, 404 path, no browser storage written for runs, `chatState` reducer cases

## 8. Settings drawer

- [x] 8.1 Build `features/settings/SettingsDrawer.tsx` on `BottomDrawer` with Assistant (OpenAI) and Data services (Census, CompTox) accordion sections; label + info tooltip, clearable password input, status line, Clear key / Reset / Save per key
- [x] 8.2 Change `useKeyStatus` to record success/error per key so each section shows its own `Banner`; Save disabled while blank or busy; input cleared after save and by Reset
- [x] 8.3 Open the Assistant section expanded when the OpenAI key is missing; connect the composer's "open Settings" and the rail's Settings entry to the drawer; remove `ApiKeyVaultModal` and `ModalSheet` once unused
- [x] 8.4 Port the existing modal tests: save/clear affect only their key, stored badge shows no key part, error banner on failure, optional-key notes, Esc and focus return, `localStorage`/`sessionStorage` hold no key

## 9. Docs and verification

- [x] 9.1 Update `frontend/CLAUDE.md` (layout, new primitives, layering) and keep root `CLAUDE.md` under 80 lines
- [x] 9.2 Run `uv run pytest`, `ruff format`, `ruff check`, `pyright`, `bandit`, the function-length check, and `npm --prefix frontend run check` and `run build`; all pass
- [x] 9.3 Manual check in the browser (`npm run build` then `uv run python -m api`): drag every splitter without map clipping, fullscreen both panels and exit with Esc, collapse/restore rail and chat, USA map on load and fly to facilities, Reset to USA view, a wide table scrolls inside the chat, Settings opens from the rail, light and dark mode, reduced motion, narrow window
- [x] 9.4 Run `openspec validate refactor-workspace-layout --strict`
