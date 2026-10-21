## Context

See proposal.md (Why) and the specs for the behaviour. Current state that shapes the approach:

- The only entry point is the CLI (`app/__main__.py` → `app/run.py::ask`), which calls
  `agent.graph.build_agent(model).invoke(...)` once. There is no web framework, no
  checkpointer, no streaming, and no Node project in the repo (Node 24 is installed locally).
- `build_agent` compiles a two-node graph (`model` ⇄ `tools` via `ToolNode`); the chat model is
  injected and built only by `app/chat_model.py`, which reads the key from `OPENAI_API_KEY`.
- Tools return TypedDicts (`tools/schemas.py`); `ToolNode` serialises them to JSON strings in
  `ToolMessage.content`. These, plus the `tool_calls` arguments on the preceding `AIMessage`,
  are the only trustworthy source of dashboard values.
- What the tools *do not* report, which the request asked for: a chemical name for the queried
  CAS (only the surrogate's name), a "TRI Facility ID" (only the TRI document control number), a
  4-tier stack provenance (sources are NEI / PSTK / AirToxScreen global default), a wind
  distribution for a rose (only an annual-mean direction), and a modelled plume footprint
  (SCREEN3 gives a centerline maximum and distance, not a 2-D field). The UI shows only what
  exists; see Decisions 9–10.
- Project rules that apply: strict pyright, ≤18-line functions, config in `settings.toml`,
  dependency direction, provider imports only in `app/chat_model.py`, prompts only in
  `prompts/*.md` via the registry, one CLAUDE.md per layer, root CLAUDE.md ≤ 80 lines.
- Prior eval findings: the agent's behaviour is sensitive to the system prompt wording (CAS
  rule), so the shared prompt and default graph must not change.

## Goals / Non-Goals

**Goals:**
- Clear three-layer separation (frontend / backend / agent core) with a single generated
  wire contract.
- Every number on screen traceable to a tool result; absent data stays visibly absent.
- Key never leaves the OS credential store except as an in-memory `SecretStr` for one turn.
- Delivered as thin, independently demoable vertical slices (see tasks.md).

**Non-Goals:**
- Multi-user hosting, authentication, remote access, HTTPS (loopback-only local tool).
- Persisting conversations or dashboards across restarts.
- New scientific capability: no plume footprint modelling, wind roses, chemical-name lookup or
  extra stack tiers (each would be a tool change with its own spec).
- Changing CLI/eval behaviour, tool descriptions or `prompts/agent_system.md`.
- Deploying the agent as a separate service (LangGraph Server) — possible later behind the same
  contract.

## Decisions

### 0. Directory layout and boundaries (user-specified, authoritative)

`api/` is a **thin HTTP/SSE transport, security and state-serialisation adapter**; it never
duplicates physics, EPA queries or read-across math (those stay in `agent/`, `tools/`,
`models/`, `data/`). Router → Service → Domain layering:

```text
api/
├── main.py              # app factory, CORS (own origin only), Origin/Host guard, lifespan
├── dependencies.py      # Depends() providers: vault, settings, thread store, per-turn key
├── core/
│   ├── config.py        # typed view over config.ui ([ui] in settings.toml)  (see deviation a)
│   ├── security_keyring.py  # keyring vault for the API (wraps app/key_vault.py) (deviation b)
│   ├── logging_filter.py    # SecretRedactionFilter + installer
│   └── exceptions.py        # sanitised handlers, correlation ids
├── schemas/             # Pydantic v2, frozen, extra="forbid": the single wire contract
│   ├── chat.py          # ChatRequest, SSE event union, GuardrailPivotResponse, usage
│   ├── workspace.py     # WorkspaceState (overview metrics, facility markers, buffer/sector GeoJSON)
│   └── settings.py      # KeyUpdatePayload (SecretStr), KeyStatusResponse, ClientConfig
├── routers/             # thin handlers, no business logic
│   ├── v1_chat.py       # POST /api/v1/chat/stream; DELETE /api/v1/chat/threads/{thread_id}
│   ├── v1_facilities.py # GET /api/v1/facilities/{frs_id}?thread_id=  (from the thread's state)
│   └── v1_settings.py   # GET/POST/DELETE /api/v1/settings/openai-key; GET /api/v1/settings/client
└── services/
    ├── agent_runner.py      # runs the graph with the per-turn SecretStr, yields SSE events
    ├── state_serializer.py  # tool calls/results -> WorkspaceState (facade)
    ├── projectors/          # one module per tool family used by state_serializer
    ├── geometry.py          # buffer circle + schematic downwind sector GeoJSON (pure)
    ├── threads.py           # in-memory checkpointer, per-thread lock, session usage
    └── usage_meter.py       # token callback + cost from [ui.pricing]
```

`frontend/` is feature-driven with one-way imports `components/ui` → `features/*` → `App.tsx`
(`hooks/` and `services/` may be used by features; `components/` import nothing from
`features/`):

```text
frontend/src/
├── main.tsx, App.tsx (locked split: left 64% / right 36%), index.css (HIG tokens)
├── components/layout/{SplitWorkspace,TopHeaderBar}.tsx
├── components/ui/{GlassCard,StatusPill,SegmentedBar,ModalSheet}.tsx
├── features/overview/{EpaOverviewRibbon,RiskMetricCard,ReadAcrossCard,DemographicsCard,MeteorologyCard}.tsx
├── features/map/{ExposureMapCanvas,PlumeSectorLayer,FacilityMarker,FacilityHoverCard}.tsx
├── features/chat/{ChatDock,MessageStream,ToolExecutionPill,ChatComposer,UsageMeter}.tsx
├── features/settings/ApiKeyVaultModal.tsx
├── hooks/{useAgentStream,useWorkspaceStore,useKeyStatus,useClientConfig}.ts
├── services/apiClient.ts           # fetch + SSE wrappers for /api/v1/*
└── types/api.ts (generated) + types/workspace.ts (named re-exports mirroring api/schemas/)
```

Vite proxies `/api` to `http://127.0.0.1:8000` in dev; `[ui].port` ships as 8000.

**Is `app/` still needed?** Yes, as the composition root. It is the only module allowed to
import a provider package (`app/chat_model.py`), and `evals/suite.py` / `evals/runner.py`
build the agent's model and run config through it, as does the CLI. Removing it would move
the provider import into `api/` (making `evals` depend on the web layer) or into `agent/`
(breaking provider-agnosticism). It stays, scoped to: chat-model factory, key resolution
(`app/key_vault.py`) and the CLI. `api` → `app`, never the reverse.

Deviations from the pasted layout, each to keep an existing project rule:
- (a) `api/core/config.py` is not a `BaseSettings` reading the environment: every setting
  lives in `config/settings.toml` with a typed loader (`config/ui.py`); the API module only
  exposes it to `Depends()`. One source of truth, no env overrides of ports/origins.
- (b) The keyring logic lives in `app/key_vault.py` so the CLI uses the same stored key (the
  "one key for agent and chat" decision); `api/core/security_keyring.py` builds that vault from
  `[ui.keyring]` and maps keychain errors to user-safe responses.
- (c) CORS is installed with `allow_origins` = the configured own origin only (dev goes
  through the Vite proxy), and the Origin/Host guard still rejects cross-site writes.
- (d) Stack tier pills show the three real tiers (user decision), not "Tier 1-4".
- (e) Added beyond the paste: `GET /api/v1/settings/client` (display settings for the
  frontend), thread reset, `UsageMeter.tsx` / `usage_meter.py` (token & cost request), and the
  `guardrail_pivot` event for redirects.
- (f) The buffer circle and schematic sector GeoJSON are built in `api/services/geometry.py`
  (pure geometry from tool-reported centre, radius and wind direction; not physics), so
  `PlumeSectorLayer.tsx` only renders `WorkspaceState`.

### 1. Three layers, one-way, in one process
```
frontend/  (React, browser)  ──HTTP + SSE (generated contract)──▶  api/  (FastAPI)
                                                                      │ in-process calls
                                                                      ▼
                                   app/ (chat-model factory, key vault) → agent/ → tools/ → models/
```
- `frontend/` is a standalone Vite project. It knows only `/api/*` and the generated types.
- `api/` is a new Python layer (layout in Decision 0): HTTP, SSE, origin checks, thread store, workspace
  projection, usage metering, redaction. Allowed imports: `app`, `agent`, `config`, `commons`,
  and `tools.schemas` (types only, for the projection). Nothing in the project imports `api`
  except `evals`-style outer edges (none today).
- The agent core is unchanged in shape; it gains two opt-in parameters and stays unaware of
  the web.
- *Alternative:* backend and agent as separate processes (LangGraph Server + proxy). That gives
  isolation the single-user local tool does not need, at the cost of a second process, a second
  key hand-off and network hops. The contract stays the same, so it can be split later.

### 2. Stack: FastAPI + React/TS/Vite/Tailwind/MapLibre/Recharts/Lucide
- FastAPI: async, Pydantic models give the JSON Schema used for the contract (Decision 4), and
  `StreamingResponse` is enough for SSE (no `sse-starlette`).
- React 18 + TypeScript strict + Vite; Tailwind with CSS-variable design tokens for the HIG
  materials, light/dark; `maplibre-gl` used directly through a small hook (no wrapper library);
  Recharts only for the age-band stacked bar; Lucide icons; `react-markdown` *without*
  `rehype-raw` for safe Markdown; Vitest + Testing Library; ESLint.
- *Rejected:* Streamlit (rerun-the-script model cannot hold a locked split shell, anchored
  glass popovers or streamed pills); CopilotKit (its LangGraph path expects its runtime, which
  normally holds the LLM key, conflicting with Decision 6, and its styling would be overridden
  almost entirely). The event vocabulary is AG-UI-like, so adopting it later stays cheap.

### 3. Streaming a turn
- `POST /api/v1/chat/stream` (body: `thread_id`, `message`) → `StreamingResponse(media_type="text/event-stream")`; the
  frontend reads it with `fetch` + `ReadableStream` (EventSource cannot POST).
- The backend runs `graph.astream(..., stream_mode=["messages", "updates"], config=...)`:
  `messages` chunks from the `model` node become `token`; `updates` from the `model` node yield
  `tool_calls` → `tool_status` (phase `started`); from `tools` yield `ToolMessage`s →
  `tool_status` (phase `finished`, status from `ToolMessage.status`, summary = label, never the
  payload), then the workspace is re-serialised and sent as `workspace_update`. A redirect from
  the `scope` node is sent as `guardrail_pivot`. Lives in `api/services/agent_runner.py`.
- The event encoder is a pure function `event → "data: {json}\n\n"`; the stream generator
  wraps the run in `try/finally` so `turn_finished` is always sent.
- Sync tools (httpx) run in `ToolNode`'s thread pool under `astream`; the agent's timeouts and
  `recursion_limit` from `[agent]` still bound the run.

### 4. Contract: Pydantic → JSON Schema → TypeScript
- `api/schemas/` holds every request, response, event and `WorkspaceState` model
  (frozen, `extra="forbid"`). `scripts/export_contract.py` writes
  `frontend/src/types/schema.json`; `npm run gen:types` (json-schema-to-typescript) writes
  `frontend/src/types/api.ts`; `types/workspace.ts` re-exports the names features use. All
  committed.
- Drift checks: a pytest asserts the exported schema equals the committed `schema.json`; the
  frontend `check` script regenerates types and fails on a diff (`git diff --exit-code`).

### 5. Threads and concurrency
- `build_agent(..., checkpointer=InMemorySaver())` keyed by `thread_id`; the backend keeps a
  `ThreadStore` with a per-thread `asyncio.Lock` (409 when held) and per-thread session usage.
  Reset deletes the checkpoint thread and the usage.
- The workspace is **a pure function of the thread's message list**
  (`serialize(messages) -> WorkspaceState`, `api/services/state_serializer.py`), recomputed
  after each tool batch. No separate workspace store can drift from the history, and follow-up turns keep earlier facilities for
  free.

### 6. API key: vault in `app/`, read per turn
- `app/key_vault.py`: a `KeyVault` protocol (`save`, `load -> SecretStr | None`, `clear`,
  `status`) and a `KeyringVault` implementation using `keyring` with the service/account from
  `[ui]`. Status is only whether a key is stored, never any part of it. Validation (non-blank, no
  whitespace/control chars, ≤ max length) happens before `keyring.set_password`.
  `keyring.errors.KeyringError`/`NoKeyringError` become a user-safe "keychain unavailable".
- `app/chat_model.py`: `build_chat_model(settings, environ=None, *, api_key: SecretStr | None)`;
  an injected key skips the environment (spec: Injected key). The SecretStr goes straight to
  `ChatOpenAI(api_key=...)`; it is never unwrapped except inside the provider.
- Per turn, the backend calls `vault.load()` once, builds one chat model, and passes that same
  model to the guard and the agent (one key for both; spec "Key read per request"). The
  compiled graph is cheap to rebuild per turn; the checkpointer is shared.
- CLI (`app/run.py`): `vault.load()` first, `OPENAI_API_KEY` otherwise, so evals/CI keep
  working headless. *Alternative rejected:* keyring-only everywhere — breaks CI and evals.
- The vault lives in `app/` (outer edge, I/O allowed) because both the CLI and the backend need
  it and `app` must not import `api`.

### 6b. One key for the tools too (user decision)
- `lookup_scc_process_description` builds its own OpenAI embeddings and used to read only
  `OPENAI_API_KEY`. To honour "one stored key for agent and chat" without touching the process
  environment, the key is passed per turn through a request-scoped holder: a generic
  `commons.scoped_secret.ScopedSecret` (a `ContextVar` with a `provide()` context manager) and
  its single instance `tools.credentials.PROVIDER_KEY`. `api/services/agent_runner.py` wraps the
  agent run in `PROVIDER_KEY.provide(key)`; LangGraph copies the context into node tasks and
  executor threads, so tools see it.
- `tools/emissions/rag/embeddings.py` resolves the key per embedding call (holder first, then
  the environment variable) through a lazy wrapper, so the cached retriever and its embeddings
  never hold a key across turns. `build_embeddings` still fails at build time when no key is
  available, as before.
- The holder is cleared with `set(None)` (not `reset(token)`) because an async generator can be
  closed from a different context on disconnect.
- *Alternatives rejected (user chose this):* copying the key into `os.environ` (inherited by child
  processes, stale after a key change); leaving the tool on the environment variable.

### 6c. Census and CompTox keys through Settings (user decision)
- The user asked for the Census and CompTox keys to be provided like the OpenAI key. The keychain
  holds three entries under one service name; `[ui.keyring]` names the service and one account
  per key (`[ui.keyring.accounts]`: `openai`, `census`, `comptox`). `app.key_vault` keeps its
  single-entry `KeyringVault` and gains `ServiceKeys`, a small holder of three vaults by name
  (`default_service_keys()`); the vault, its validation and masking are unchanged.
- API: the OpenAI routes stay (`/api/v1/settings/openai-key`), `census-key` and `comptox-key`
  mirror them, and `GET /api/v1/settings/keys` returns the three statuses at once (one fetch
  for the sheet). Routes are registered from one table so a key is one entry, not one copy.
- Per turn the runner reads the OpenAI key (required) and, when stored, the other two once, and
  provides them to tools through `tools.credentials` (`PROVIDER_KEY`, `CENSUS_KEY`,
  `COMPTOX_KEY`, all `ScopedSecret`s). The population and CompTox tools resolve their key per
  call (holder first, then the existing environment variable), and the CompTox client no longer
  keeps anything key-shaped between calls. Missing optional keys are not an error of the turn:
  the tools already report a missing key (screening default with a warning; a setup error from
  the CompTox lookup, shown to the model as a tool error).
- The CLI provides stored keys the same way around its run (`app.run.ask`), with the environment
  as fallback per key; evaluations are unchanged (environment only).
- Log redaction: the OpenAI pattern cannot match the other two, so the runner registers the
  turn's stored values with the redaction filter (a per-turn set matched literally and removed
  at the end of the turn).
- The `.env` file is still loaded at start for the variables the tools name, so keys there keep
  working as the fallback.
- *Alternatives rejected (user chose this):* keeping both in `.env` only; putting them in
  `settings.toml` (contradicts "secrets kept out of configuration").

### 7. Redaction and leak-free errors
- `api/core/logging_filter.py`: `SecretRedactionFilter(logging.Filter)` rewrites
  `record.msg` to the fully formatted, redacted message, clears `record.args`, and pre-renders
  and redacts `exc_info`/`stack_info` into `record.exc_text`/`stack_info`; returns `True` always.
- Logger-level filters do not see records propagated from child loggers, so the installer adds
  the filter to the named loggers (root, `uvicorn`, `uvicorn.error`, `uvicorn.access`, `httpx`,
  `httpcore`) **and** to every handler of the root and uvicorn loggers, via the uvicorn
  `log_config` passed at launch.
- Exception handlers: `Exception` → 500 `{"error": "Internal error", "correlation_id": ...}`
  with the redacted traceback logged; `RequestValidationError` → 422 listing field locations and
  messages only (the `input` values are stripped). The same correlation id goes in SSE `error`.
- Origin/Host middleware (server spec: Cross-site requests are rejected): exact match on
  `http://{host}:{port}`; CORS middleware is not installed.

### 8. Scope guardrail in `agent/guardrails.py`
- `ScopeGuard` (frozen dataclass): classifier prompt text, fallback redirect text, history
  window. `build_agent(..., scope_guard=None)`; when given, the graph is
  `START → scope → (in: model | out: END)` and `scope` appends nothing for in-scope turns, or an
  `AIMessage(reply, name="scope_redirect")` for out-of-scope turns.
- The classifier call is `model.with_structured_output(ScopeVerdict, include_raw=True)` on the
  system classifier prompt plus the last *n* messages (text only; tool messages summarised by
  name) — the raw message keeps usage metadata for Decision 11. One call returns both verdict and
  the redirect text, so a redirect costs one call total.
- Fail-open on exception or unparseable verdict (spec explains why), logged as a warning.
- The backend loads `prompts/scope_classifier.md`, `prompts/scope_redirect_fallback.md` and
  `prompts/scope_addendum.md` through `prompts.registry` (names from `[ui]`) and builds the
  system prompt as `agent_system + "\n\n" + scope_addendum`. Prompts follow the repo's XML
  structure and the "teach reasoning, never name tools" rule.
- *Alternatives:* keyword gate (brittle for follow-ups), prompt-only (cannot guarantee "no tools
  run"). Chosen by the user.

### 9. Workspace serialisation (`api/services/state_serializer.py` + `projectors/`)
- Pairs each `AIMessage.tool_calls[i]` with its `ToolMessage` by `tool_call_id`, then dispatches
  on tool name through a table `{tool_name: projector}` (open/closed: a new tool is one entry;
  a test asserts every key is a registered tool name, so renames fail loudly).
- Each projector validates its payload with a strict Pydantic model mirroring the TypedDict
  (finite floats, `StrictBool`/no bool-as-number, coordinate ranges); failures become dashboard
  warnings, never exceptions.
- Attribution uses identifiers only (spec: Facilities). Receptor matching uses the configured
  coordinate tolerance because the agent passes the inventory's lat/lon through; exposure
  results match on exactly-one equal emission rate. Anything else is "unattributed".
- Stack tiers: NEI → "Tier 1: Empirical NEI", PSTK → "Tier 2: PSTK by SCC" (+ SCC description
  and score when an SCC lookup in the thread returned it), global default → "Tier 3: EPA global
  default". Chosen by the user over adding a 4th tier in the tools.
- Fields the tools don't have are labelled honestly: "TRI doc. control no." instead of TRI
  Facility ID; no queried-chemical name (surrogate name only); meteorology shows a single
  downwind arrow, not a rose.

### 10. Map rendering
- Carto Positron / Dark Matter GL style URLs from `[ui]`, switched with `prefers-color-scheme`,
  attribution shown. Facilities as a GeoJSON source with circle layers: colour by risk status
  (neutral when uncomputed), radius by `emission_rate` on a configured sqrt scale.
- Camera: `fitBounds` with padding when `framing_version` changes; `duration: 0` under
  reduced motion.
- Buffer circle and downwind sector are generated in `api/services/geometry.py` as GeoJSON
  polygons from the tool-reported centre, radius and wind direction and the configured
  half-angle (pure geometry, pytest-tested), carried in `WorkspaceState`, and drawn by
  `PlumeSectorLayer.tsx`. The sector is always labelled schematic.
- Inspector: a React portal positioned from `map.project(lngLat)`, opened on `mouseenter`
  and on focus of an invisible, keyboard-focusable button per marker (MapLibre canvas markers
  are not focusable), closed on leave/blur/Escape.

### 11. Usage and cost
- `api/services/usage_meter.py`: a `BaseCallbackHandler` passed in the run config records `on_llm_end`
  usage from each generation's `AIMessage.usage_metadata` (input, `input_token_details.cache_read`,
  output) plus model name, for classifier and agent calls alike; missing metadata → "unknown"
  and the turn is flagged incomplete.
- Cost is a pure function `(usage, PriceTable) -> Cost | None` in `api/services/usage_meter.py`;
  `cached` tokens are billed at the cached price and subtracted from input.
- `[ui.pricing."<model>"]` entries hold `input_usd_per_mtok`, `cached_input_usd_per_mtok`,
  `output_usd_per_mtok`, `priced_on`, `source_url`. Values are copied during implementation from
  the provider's published price page (task 6.x) — never typed from memory. If they cannot be
  verified, the model ships unpriced and the UI says so.

### 12. Display thresholds
- HQ threshold of concern 1.0 (EPA's non-cancer benchmark). "Near" band lower bound in config
  (shipped 0.5, a display choice, commented as such).
- Cancer risk: below 1 × 10⁻⁶, near between 1 × 10⁻⁶ and 1 × 10⁻⁴, above 1 × 10⁻⁴ (EPA's
  acceptable-risk range), commented with that basis.

### 13. Tooling and layer rules
- New `api/CLAUDE.md` and `frontend/CLAUDE.md`; root CLAUDE.md lists them and the new
  dependency direction in ≤ 80 lines (move detail into the folder files).
- `api` added to the pyright `include`, bandit target, function-length hook `files` regex
  and the root CLAUDE.md commands. A pre-commit `frontend-check` hook runs
  `npm --prefix frontend run check` (tsc, eslint, vitest, contract diff) only when
  `frontend/` files change.
- `.gitignore`: `frontend/node_modules/`, `frontend/dist/`.
- Launch: `npm --prefix frontend ci && npm --prefix frontend run build`, then
  `uv run python -m api`; README documents both.

## Risks / Trade-offs

- [Classifier adds latency and cost to every turn] → small prompt, short history window,
  usage shown in the meter; the in-scope path adds one short call.
- [Classifier false positives refuse legitimate questions] → broad in-scope list with
  conversational turns explicitly in scope; unit tests with a fake model for each category;
  the user can rephrase and the redirect offers domain pivots.
- [Attribution heuristics (emission-rate / coordinate matching) mis-assign results] → fail
  closed: ambiguity → "unattributed", shown in a warnings list, never guessed.
- [`astream` message chunking differs across LangChain versions] → isolate the stream adapter
  in one module with tests driven by a fake streaming chat model.
- [Keychain prompts / unavailable backend on Linux CI] → tests use an in-memory fake keyring
  backend; the real backend is only touched at runtime.
- [Basemap tiles are an external dependency] → map degrades to a blank canvas with markers and
  a notice; the ribbon and chat keep working.
- [Prices go stale] → `priced_on` shown in the meter popover; cost always labelled estimate.
- [Frontend toolchain adds Node to the dev loop] → only needed to build; the backend fails with
  a clear message when `dist/` is missing.
- [Root CLAUDE.md 80-line limit] → detail goes in the new folder CLAUDE.md files.

## Migration Plan

Additive. The CLI, evals and default graph are unchanged (new parameters default to `None`),
so no migration. Rollback: delete `api/`, `frontend/`, the `[ui]` table and the new prompts,
and revert the two optional parameters and the injected-key argument. After implementation,
optionally run the eval suite once to confirm the default path is untouched (costs tokens; ask
first).

## Open Questions

- Exact Carto style URLs and attribution text: verify the current public endpoints during
  implementation (config only; no spec impact).
