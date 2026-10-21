# frontend/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `frontend/`.

- React + TypeScript (strict) + Vite + Tailwind; MapLibre GL for the map, Recharts for the
  age-band bar, Lucide for icons. Commands: `npm --prefix frontend ci`, `run build`,
  `run check` (contract diff, tsc, eslint, vitest). `check` must pass before work is done.
- Feature-driven layout with one-way imports: `components/` (`layout/`, `ui/`: domain-agnostic
  HIG primitives) -> `features/` (`overview/`, `map/`, `chat/`, `settings/`) -> `App.tsx`.
  `hooks/` (stream, stores, key status) and `services/apiClient.ts` serve features;
  `components/` never import `features/`, and features never import each other's internals.
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
  them, not literal colours. Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Pure helpers (formatting, SSE parsing, store reducers) get Vitest tests beside them.
