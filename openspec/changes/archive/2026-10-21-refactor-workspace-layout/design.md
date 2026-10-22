## Context

See `proposal.md` for motivation and `specs/` for requirements. Current state:

- `SplitWorkspace` is a fixed CSS grid (64fr/36fr) with `left` (an `OverviewPane` holding the
  ribbon and the map in one scrolling column) and `right` (`ChatDock`).
- Settings is `ApiKeyVaultModal` inside `ModalSheet`, opened by a gear in `TopHeaderBar`. The
  key hooks (`useKeyStatus`) and endpoints (`/api/v1/settings/{openai,census,comptox}-key`,
  `/keys`) already exist and stay as they are.
- `ExposureMapCanvas` already starts on the configured `initial_view` (the US), but it is only
  mounted once `ClientConfig` has loaded (a "Loading the map…" card before). It never calls
  `map.resize()`. MapLibre only listens to window resize, so a splitter drag leaves it stale.
- `useAgentStream` owns one thread id and `reset()` deletes the thread on the server.
  `ThreadStore` keeps history (in the LangGraph `InMemorySaver`), tool messages, usage and the
  workspace per thread, with no cap and no read API.
- The reference Settings page in `../anl/desktop-greet` is MUI + MobX + an internal
  `@shared-frontend` kit (Accordion, BasicDrawer, Input, InfoTooltip, WarningMessage). None of
  that exists here. Its UX is portable; its code is not.
- Constraints from `frontend/CLAUDE.md`: Tailwind with CSS-variable tokens, one-way layering
  (`components/` never imports `features/`), display settings only from `/settings/client`, no
  key material in browser storage, no raw HTML in Markdown.

## Goals / Non-Goals

**Goals:**
- One resizing mechanism for all splitters, with consistent keyboard and ARIA behavior.
- The map is never unmounted or recreated by layout changes (fullscreen, collapse), only resized.
- Run history that stays inside the "in memory, never on disk" rule.

**Non-Goals:**
- Persisting runs across a server restart or a page reload.
- Provider settings beyond the three keys: no base URL, model name or Test Connection.
- Restoring tool-step pills for past turns (the server stores no tool-status events).
- Drag-and-drop docking or re-ordering of panels.
- A UI component library. The MUI look is not reproduced; the structure and interaction are.

## Decisions

### 1. `react-resizable-panels` for splitters
Use `react-resizable-panels` (pinned exact version) with nested groups: horizontal
`[rail | analysis | chat]`, and inside the analysis panel a vertical `[overview | map]`. Library
panels give pointer capture, keyboard resizing, `role="separator"` with `aria-valuenow`, imperative
`collapse()`/`expand()`/`resize()` and `autoSaveId` persistence (sizes only, in `localStorage`).
Custom sashes would re-implement all of that and its edge cases.
*Alternative:* hand-written pointer-capture sashes. Rejected: more code, more a11y risk, and the
repo's 18-line limit applies to Python only but tests would still be heavier.

The sash is one small `PanelSplitter` in `components/layout/` (a 1 px hairline widening to a 3 px
accent line on hover, focus and drag, using the existing accent token). The library's size units
are percentages, and limits are px or shares. So `SplitWorkspace` converts the configured limits
with the measured group width (via `ResizeObserver`) before passing them as `minSize`/`maxSize`.
Restored sizes pass through the same clamp, which covers "restored size out of range".

### 2. Layout limits come from `[ui.layout]`, served in the client config
Add `[ui.layout]` to `settings.toml`, a frozen dataclass in `config/ui.py`, validated (min ≤
default ≤ max, shares in (0, 1), positive ints), and a `LayoutConfig` model in
`api/schemas/settings.py` exposed in `ClientConfig`. Until the config arrives the shell renders
the panels with a conservative built-in skeleton (equal-ish panel proportions, no numbers that
look like settings), so the map can mount immediately. The layout limits are applied the moment
config arrives.
*Alternative:* hard-code limits in TS. Rejected by `frontend/CLAUDE.md` and the existing
app-configuration requirement.

### 3. The map mounts without waiting for config
`MapPanel` renders `ExposureMapCanvas` once `config.map` exists, as today, but the panel shell
(header, fullscreen, reset button) and a blank-canvas background render at once, so there is
never an empty hole. The "Loading the map…" card is placed inside the Map panel, not in place of
the layout. The first frame after config is the US view. (The map needs the style URLs from config,
so it cannot start before the config loads. That is unavoidable and brief.)

### 4. Resize tracking in the map component
`ExposureMapCanvas` owns a `ResizeObserver` on its container, created in the same effect as the
map and disconnected on cleanup. The callback coalesces calls with `requestAnimationFrame` and
calls `map.resize()`. No other component knows about the map. Fullscreen, collapse and drag all
reach it by changing the container size. MapLibre keeps its camera across `resize()`, so there is
no jitter. The existing `fakeMaplibre` test double gains `resize`, and jsdom gets a
`ResizeObserver` stub in `test/setup.ts`.
*Alternative:* have the layout call a map ref after each change. Rejected: couples layout to the
map and misses window or devtools resizes.

"Reset to USA view" is a button in a small map toolbar. It calls `fitBounds(initial_view)` with the
same padding and reduced-motion handling as the framing effect. Facility framing keeps its
`framing_version` trigger, so new data does not fight a user who has panned away.

### 5. Fullscreen without remounting
Fullscreen is a layout state (`"overview" | "map" | null`) in `SplitWorkspace`. Instead of
conditionally rendering a different tree (which would destroy the MapLibre instance), the
fullscreen panel is made to fill the workspace with CSS: the other regions are `hidden`
(`display:none`) and the group's other panels are collapsed. Since the DOM stays, the map keeps
its instance, and the observer from decision 4 handles the new size. `Esc` is handled with one
`keydown` listener that ignores the event if it was already handled (`defaultPrevented`) by the
inspector or drawer, which call `preventDefault()` when they close.
*Alternative:* the browser Fullscreen API. Rejected: it hides the app chrome and needs a user
gesture per call, and the request is about the workspace, not the screen.

### 6. Chat dock collapse
The chat panel is a library collapsible panel (`collapsible`, `collapsedSize=0`). The header has a
collapse button. When collapsed, a slim edge tab on the right restores it to the remembered size.
Chat state lives in `App` hooks, so collapsing unmounts nothing. The composer draft therefore
survives (the panel is hidden, not removed).

### 7. Navigation rail
`LeftNavRail` is a controlled component: `{collapsed, onToggle, runs, currentId, onNewAnalysis,
onSelectRun, onOpenSettings}`. It lives in `components/layout/` and takes plain props, so it does
not import features (layering test). Collapsed = a library panel at `collapsedSize` (configured
~60 px) and expanded = resizable within 200–320 px. Entries are `<button>`s with `aria-label`
and a CSS tooltip when collapsed; the current run has `aria-current="true"`. Below the narrow
breakpoint the rail forces the collapsed state.

### 8. Run history: keep threads server-side, list them client-side
- **Client:** a `useRunHistory` hook holds `{id, title, createdAt}[]` in React state only (never
  in browser storage). `useAgentStream` is changed to take the active thread id from the hook;
  "New analysis" creates a new id and does not call `DELETE`. Selecting a run calls
  `GET /chat/threads/{id}`, loads the messages into the chat reducer (new `restore` action),
  applies the workspace through `onWorkspace` (which bumps framing so the map frames it), and
  sets the thread active. A run is not switchable while `busy` (the rail disables other runs).
  The title is the first user message, cut to a configured-free fixed length in the UI component,
  which is presentation, not a setting.
- **Server:** `ThreadStore` gets an access order (`OrderedDict`) and a max size from `[ui.threads]
  max_retained`. `claim()` is the "touch" point. Before adding a new id, if the store would exceed
  the max, evict the oldest idle id with the same cleanup as `reset`. `snapshot(thread_id)`
  returns text-only `HumanMessage`/`AIMessage` (no tool calls, non-empty content) from the
  checkpointer's `messages` channel, the workspace, and the usage totals. The route is a thin
  handler in `v1_chat.py`; the schema `ThreadSnapshot` is in `api/schemas/chat.py` and reuses
  `WorkspaceState` and the usage totals model. Unknown thread → 404 through the existing
  exception handlers, so the body stays generic.
- Guardrail pivots (off-topic redirects) are written into the history by the agent graph; if the
  graph does not store them as `AIMessage`s the snapshot would miss them. The tasks check this
  and add the pivot to the snapshot source if needed.

*Alternative considered:* client-held snapshots only (no backend change). Rejected by the user in
favor of resumable runs. *Alternative:* persisting to disk. Rejected: violates the spec.

### 9. Settings drawer, ported by structure
`features/settings/SettingsDrawer.tsx` replaces `ApiKeyVaultModal`:
- `components/ui/BottomDrawer` (resizable by a top sash using the same `PanelSplitter` logic or a
  pointer-capture handle, maximize toggle, focus trap and Esc taken from `ModalSheet`). Because
  `ModalSheet`'s trap is the only one in the code, extract `useFocusTrap` into `components/ui/`
  and use it in both, then delete `ModalSheet` once nothing uses it.
- `components/ui/Accordion` (multi-open, `aria-expanded`), `InfoTooltip` (focusable, `role=
  "tooltip"` via `aria-describedby`), `Banner` (`role="status"` success / `role="alert"` error).
- Sections: "Assistant" (OpenAI), "Data services" (Census, CompTox). Each key row = label +
  tooltip, password input with a clear (×) button, status line, "Clear key", Reset (clears the
  draft) and Save. Per-section banners show the result of the last action of that key; the
  existing `useKeyStatus` `error` is split per key (the hook records `{name, message}`), which
  also fixes the current shared error line.
- The drawer height (not content) may be saved in `localStorage` for convenience; no key
  material ever is. A test asserts storage holds no key after saving.
- The Assistant section opens expanded when the OpenAI key is missing; the chat composer's
  "open Settings" calls the same `onOpenSettings`.

### 10. GFM tables in the chat
Add `remark-gfm` (pinned) to `Markdown`'s `remarkPlugins`; raw HTML stays off (react-markdown
default, no `rehype-raw`). Map `table` to a wrapper `div` (`overflow-x-auto max-w-full my-3
rounded-xl border`) around a `<table>`. Header and cell styles are set by `components` overrides
on `thead/th/td/tr` using the project's tokens (`border-hairline`, a token-based shaded header
instead of literal `black/[0.03]`, since colors must come from tokens). `tabular-nums` applies to
the whole table, and `whitespace-nowrap` to all cells (the scroll container handles overflow,
so wrapping prose columns is not needed). The message bubble gets `min-w-0` so the flex child can
shrink and the table scrolls rather than stretching the dock.
*Alternative:* `whitespace-nowrap` only on numeric columns. Rejected: needs per-column detection;
the content (CAS, units, HQ) is mostly short, and the user can scroll.

### 11. Narrow viewport
Below the breakpoint the rail is forced to icons and the analysis area / chat swap through the
existing segmented control. Splitters are not rendered in the stacked layout. The same panel
instances stay mounted (hidden with CSS), as today.

## Risks / Trade-offs

- [Library percent units vs px limits] → Convert with the measured group width and re-clamp on
  window resize; unit-test the conversion as a pure function.
- [Fullscreen via CSS hide leaves hidden panels in the DOM] → Intentional (keeps map and chat
  state); hidden regions get `aria-hidden` and `inert` so they are skipped by assistive tech and
  focus.
- [Resizing floods `map.resize()`] → rAF coalescing; MapLibre resize is cheap, and no overlays are
  rebuilt on resize.
- [Restored runs lose tool pills and any unrecorded guardrail text] → Documented in the spec;
  the snapshot is text and workspace only.
- [Eviction surprises a user who clicks an old run] → The 404 path removes the run and says why;
  `max_retained` is configurable.
- [Memory growth from retained threads] → Capped by `max_retained`; each held thread is the same
  size it would already be today.
- [Two scroll/resize systems fight in `OverviewPane`] → The ribbon scrolls inside the Overview
  panel; the Map panel never scrolls (it fills its panel), so no nested scroll with the map.
- [Esc handling across layers] → One rule (`defaultPrevented`), tested for inspector, drawer and
  fullscreen.
- [New dependencies] → Both are widely used; versions pinned exactly, lockfile updated, and
  `npm audit` checked in the verification task.

## Migration Plan

1. Backend first (config, thread retention, snapshot route), then re-export the contract and
   regenerate frontend types; the old frontend keeps working because the change is additive.
2. Frontend: primitives, shell, panels, then rail and history, drawer, map and tables.
3. Remove `ApiKeyVaultModal`, `ModalSheet` (if unused) and the gear from `TopHeaderBar`.
4. Rollback: revert the commit(s). No data migration, since nothing persists beyond UI sizes in
   browser storage, which older builds ignore.

Update `openspec/specs` through the normal archive. `docs/` and `frontend/CLAUDE.md` get a note
on the layout and the new primitives.
