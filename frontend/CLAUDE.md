# frontend/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `frontend/`.

- React + TypeScript (strict) + Vite + Tailwind; MapLibre GL for the map, Recharts for the
  age-band bar, Lucide for icons (react-icons only for the `TbMessageChatbot` copilot toggle).
  Commands: `npm --prefix frontend ci`, `run build`, `run check` (contract diff, tsc, eslint,
  vitest). `check` must pass before work is done.
- Feature-driven layout with one-way imports: `components/` (`layout/`, `ui/`: domain-agnostic
  HIG primitives) -> `features/` (`overview/`, `map/`, `chat/`, `settings/`) -> `App.tsx`.
  `hooks/` (stream, stores, key status) and `services/apiClient.ts` serve features;
  `components/` never import `features/`, and features never import each other's internals.
- Layout: `components/layout/SplitWorkspace` divides the window into rail | analysis (overview
  over map) | chat with `react-resizable-panels` splitters. Limits come from `layout` in the
  client config, never from constants. Fullscreen is CSS only (nothing unmounts; the others go
  `inert`), so the map keeps its camera and the chat its stream. The map watches its own
  container with a `ResizeObserver`; nothing else calls `map.resize()`. Escape belongs to the
  topmost layer: a layer that handles it calls `preventDefault()` and `stopPropagation()`.
- Browser storage holds panel sizes only (through `lib/safeStorage`, which never throws); never
  keys, runs or messages. The run list is React state; the conversations live on the server.
- Talk to the system only through `/api/v1/*` via `services/apiClient.ts`; never call tools,
  the agent or assessment services directly. Only basemap tiles are fetched by the browser.
- `src/types/api.ts` is generated from `src/types/schema.json` (exported from `api/schemas/`);
  never edit it by hand, regenerate with `npm run gen:types`. `types/workspace.ts` only
  re-exports names from it.
- Show only values the API sent. Never compute, estimate or convert scientific values; an
  absent value renders as "not reported" (or its reason), never as 0 or "-".
- Display settings (thresholds, chips, digits, map styles) come from
  `GET /api/v1/settings/client`; never hard-code them.
- Never write the API key (or any part of it) to localStorage, sessionStorage, the URL or the
  console; clear the key input after saving. Render assistant Markdown without raw HTML.
- Design tokens live as CSS variables in `src/index.css` (light and dark); components use
  them, not literal colours. The one exception is the EcoFate mark (`components/ui/BrandLogo`),
  whose fixed artwork colours match `public/logo.svg` and `public/favicon.svg`. Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Pure helpers (formatting, SSE parsing, store reducers) get Vitest tests beside them.
