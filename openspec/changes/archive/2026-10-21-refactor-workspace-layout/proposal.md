## Why

The split-screen shell from `add-split-screen-web-ui` is fixed at a 64/36 split. The overview and
the map are stacked in one scrolling column, Settings is a small modal behind a gear, and the
chat's Markdown tables come out cramped and unparsed (no GFM). An assessor working on a map
wants to give it the space, put the chat away, come back to an earlier run and read wide
scientific tables without breaking the layout. The map also waits on a "Loading the map…"
placeholder and never resizes when its container changes.

## What Changes

- **BREAKING (UI layout)**: the locked 64/36 split is replaced by a three-region resizable
  workspace: a left navigation rail, a center analysis area and a right chat dock, separated by
  VS Code-style splitters (hover/drag accent line, `col-resize`/`row-resize` cursor, keyboard
  resizing, min/max limits from configuration). Panel sizes are remembered per browser for
  convenience only. The narrow-viewport segmented fallback stays.
- New **left navigation rail** (`components/layout/LeftNavRail.tsx`), Gemini/macOS-sidebar
  style: collapsed icon rail (~60 px) or expanded and resizable (200–320 px); toggle at the top
  with the brand mark; a "New analysis" action; an analysis area with the Workspace entry and a
  list of this session's runs; Settings anchored at the bottom.
- **Center analysis area** split into an **Overview panel** and a **Map panel**, each with a
  header and separated by a draggable horizontal sash. Each panel has a fullscreen toggle
  (`Maximize2`/`Minimize2`) that fills the workspace; `Esc` exits.
- **Chat dock** can be collapsed to the right edge and restored with one click, and resized
  between a minimum width in px and a maximum share of the viewport.
- **Session run history, resumable**: "New analysis" starts a new thread and keeps the old one
  instead of deleting it. The rail lists this session's runs, and picking one restores its
  messages and map and lets the user keep chatting. A new read-only endpoint
  `GET /api/v1/chat/threads/{thread_id}` returns a thread's text messages, workspace and session
  usage. The server keeps at most a configured number of threads in memory, still never on
  disk, and evicts the oldest idle ones first.
- **Settings drawer** ported from desktop-greet's Settings page: a resizable, maximizable
  bottom drawer opened from the rail. It has accordion sections (Assistant: the OpenAI key;
  Data services: the Census and CompTox keys), labels with info tooltips, clearable password
  inputs, inline success/error banners, and Reset/Save actions. It uses the existing
  `/api/v1/settings/*-key` endpoints. There is no Test Connection and no base URL or model
  field. The top-right gear and the modal sheet are removed.
- **Map always visible**: the basemap renders on mount framed on the contiguous United States
  (configured `initial_view`), even with no facilities. A `ResizeObserver` calls `map.resize()`
  whenever a splitter, collapse or fullscreen changes the container size. A "Reset to USA view"
  control sits on the map toolbar. Facilities placed by `workspace_update` animate the camera as
  before.
- **Chat tables**: `react-markdown` with `remark-gfm`. Each table sits in its own horizontal
  scroll container, with a shaded uppercase header, tabular numerals, zebra rows, 1 px dividers
  and no wrapping inside cells. Raw HTML stays disabled.
- New dependencies: `react-resizable-panels`, `remark-gfm` (exact pinned versions).

## Capabilities

### New Capabilities
<!-- none: the layout, rail and drawer are requirements of the existing web UI shell -->

### Modified Capabilities
- `web-ui-shell`: the locked split-screen shell becomes a resizable workspace, with new
  requirements for the navigation rail, the panel fullscreen, the chat collapse and the run
  history. The map requirement adds the always-visible US view, resize tracking and the
  reset-view control. The copilot chat requirement moves Settings to the rail and adds GFM
  table rendering. The settings sheet requirement becomes a settings drawer.
- `web-ui-server`: conversation threads are kept (bounded, in memory) after a new analysis
  starts, and a read-only thread snapshot endpoint is added.
- `app-configuration`: the web UI settings gain the layout limits (rail, chat dock, analysis
  split) and the maximum number of retained threads.

## Impact

- **Frontend**: `App.tsx`, `components/layout/` (new `LeftNavRail`, `PanelSplitter`/panel
  header, rewritten `SplitWorkspace`; `TopHeaderBar` loses the gear), `components/ui/` (new
  `BottomDrawer`, `Accordion`, `InfoTooltip`, `Banner`; `ModalSheet` removed if unused),
  `features/overview/OverviewPane.tsx` (split into panels), `features/map/ExposureMapCanvas.tsx`
  (resize observer, reset view, no config placeholder gap), `features/chat/` (`ChatDock`
  collapse, `MessageStream` GFM tables), `features/settings/` (drawer replaces
  `ApiKeyVaultModal`), `hooks/useAgentStream.ts` (switch threads, restore snapshot), new
  `hooks/useRunHistory.ts`, `services/apiClient.ts` (`getThread`), regenerated `types/api.ts`.
- **Backend**: `api/routers/v1_chat.py` (GET snapshot route), `api/services/threads.py`
  (bounded retention, eviction, listing a thread's text messages), `api/schemas/chat.py`
  (`ThreadSnapshot`), `config/settings.toml` + `config/ui.py` (`[ui.layout]`, `[ui.threads]`),
  `api/schemas/settings.py` (layout limits in the client config).
- **Contract**: `schema.json` re-exported; frontend types regenerated.
- **Dependencies**: `react-resizable-panels`, `remark-gfm` added to `frontend/package.json`.
- **Not affected**: tools, models, agent graph, prompts, key storage and redaction.
