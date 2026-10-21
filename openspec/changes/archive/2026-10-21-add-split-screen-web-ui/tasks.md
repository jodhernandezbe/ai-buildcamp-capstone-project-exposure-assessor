Delivered as minimum viable slices. Each slice ends runnable (`npm --prefix frontend run build`
then `uv run python -m api`) with every gate green (pytest, ruff format/check, pyright,
bandit, function length, `npm --prefix frontend run check`), and can be demoed on its own.
Gates task = run all of them and fix before starting the next slice. File layout follows
design.md Decision 0 (`api/` Router → Service → Domain; feature-driven `frontend/src/`).

## 0. Foundations (layers, config, tooling)

- [x] 0.1 Add `fastapi`, `keyring` and `uvicorn[standard]` with `uv add`
- [x] 0.2 Create `api/` package (`__init__.py`, `__main__.py` stub) and `tests/api/__init__.py`; write `api/CLAUDE.md` (layer rules, allowed imports, no domain logic)
- [x] 0.3 Scaffold `frontend/` (Vite React-TS strict, Tailwind, ESLint, Vitest + Testing Library, maplibre-gl, recharts, lucide-react, react-markdown, json-schema-to-typescript) with `check`, `build`, `gen:types` scripts; write `frontend/CLAUDE.md`
- [x] 0.4 Update root `CLAUDE.md` (layers, dependency direction `frontend → api → app/agent/config`, folder CLAUDE.md list, commands) staying ≤ 80 lines; update pyright `include`, bandit targets, function-length hook regex, add pre-commit `frontend-check` hook, `.gitignore` for `frontend/node_modules/` and `frontend/dist/`
- [x] 0.5 Add `[ui]` table to `config/settings.toml` and `config/ui.py` typed loader with tests in `tests/config/test_ui_settings.py` including every invalid-entry case
- [x] 0.6 Gates
- [x] 0.7 Align with Decision 0: `[ui].port` 8000, Vite dev proxy `/api` → `http://127.0.0.1:8000`, `api/CLAUDE.md` describes Router → Service → Domain and the thin-adapter rule, `frontend/CLAUDE.md` describes `components/ui → features/* → App.tsx`; generated types move to `frontend/src/types/`

## 1. MVP 1 — Secure key + streamed chat end-to-end

- [x] 1.1 `app/key_vault.py`: `KeyVault` protocol + `KeyringVault` (validate, save, load → `SecretStr | None`, clear, status with masked hint, keychain-unavailable error); tests in `tests/app/test_key_vault.py` with a fake keyring backend
- [x] 1.2 `app/chat_model.py`: optional injected `api_key: SecretStr`; tests for injected key (env not read) and existing missing-key case
- [x] 1.3 `app/run.py`: CLI resolves the key vault-first then env; tests for both scenarios and that no `api` module is imported
- [x] 1.4 `agent/graph.py`: optional `checkpointer` parameter (default unchanged); test default graph is unchanged and a follow-up turn sees history
- [x] 1.5 `api/core/logging_filter.py` (`SecretRedactionFilter` + installer for named loggers and handlers) with tests in `tests/api/core/` for message, args, exception, short `sk-` cases
- [x] 1.6 `api/schemas/{chat,workspace,settings}.py` (ChatRequest, SSE event union, KeyUpdatePayload, KeyStatusResponse, ClientConfig, `WorkspaceState` placeholder); `scripts/export_contract.py`; committed `frontend/src/types/schema.json` + generated `api.ts` + `workspace.ts` re-exports; pytest drift check
- [x] 1.7 `api/core/config.py` (typed view over `config.ui`), `api/core/security_keyring.py` (vault from `[ui.keyring]`, error mapping), `api/core/exceptions.py` (generic handlers with correlation ids), `api/dependencies.py`, `api/main.py` app factory (own-origin CORS, Origin/Host guard, lifespan installs redaction, static `dist/` serving)
- [x] 1.8 `api/routers/v1_settings.py`: `GET/POST/DELETE /api/v1/settings/openai-key`, `GET /api/v1/settings/client`
- [x] 1.9 `api/services/threads.py` (in-memory checkpointer, per-thread lock → 409, reset) and `api/services/agent_runner.py` (astream adapter → `turn_started`, `token`, `assistant_message`, `error`, `turn_finished`; key read once per turn; no-key error); `api/routers/v1_chat.py` (`POST /api/v1/chat/stream`, `DELETE /api/v1/chat/threads/{thread_id}`); tests with a fake streaming chat model
- [x] 1.10 Per-turn key for the SCC embeddings (design 6b): `commons/scoped_secret.py` + `tools/credentials.py` (`PROVIDER_KEY`), lazy per-call key resolution in `tools/emissions/rag/embeddings.py`, `agent_runner` wraps the run in `PROVIDER_KEY.provide(key)`; update `tools/CLAUDE.md`, `tools/emissions/rag/CLAUDE.md`, `api/CLAUDE.md`; tests incl. a probe tool seeing the turn's key through LangGraph, key cleared after the turn, concurrent turns isolated
- [x] 1.11 `api/__main__.py`: loopback-only uvicorn launch with redacting `log_config`; exits with build hint when `dist/` is missing
- [x] 1.12 `tests/api/test_security_keyring.py`: keyring save/load/delete calls, redaction across records and exception messages, no `GET` endpoint returns the key (only `configured` + `masked_hint`), foreign `Origin`/`Host` → 403, error bodies leak nothing
- [x] 1.13 Frontend: `index.css` tokens (light/dark, materials, hairlines, font stack, tabular nums, spring easing); `components/layout/{SplitWorkspace,TopHeaderBar}`, `components/ui/{GlassCard,ModalSheet}`; `services/apiClient.ts` (fetch + SSE parser); `hooks/{useAgentStream,useKeyStatus,useClientConfig}`; `features/chat/{ChatDock,MessageStream,ChatComposer}` with safe Markdown; `features/settings/ApiKeyVaultModal`; placeholder left pane
- [x] 1.14 Vitest: SSE parser, vault modal clears input and never touches web storage, Markdown renders `<script>` as text, `components/` never import `features/`
- [x] 1.15 Gates (ruff, pyright, bandit, function length, pytest, frontend check, detect-secrets); the live demo with a real key (save it in Settings, ask "Assess CAS 71-43-2", see the streamed answer) needs the user's key and tokens, so it is done by the user or with their go-ahead, and repeated in 8.4

## 2. MVP 2 — Tool step pills + onboarding

- [x] 2.1 `agent_runner` emits `tool_status` started (configured label, fallback tool name) and finished (status, summary, no payload); tests incl. unlabelled tool and tool error
- [x] 2.2 `features/chat/ToolExecutionPill` collapsible per-turn row (running/done/error) and onboarding chips in `MessageStream` from the client config; "New assessment" resets the thread
- [x] 2.3 Vitest for pill grouping and chip submission; Gates

## 3. MVP 3 — Token consumption and money spent

- [x] 3.1 `api/services/usage_meter.py`: callback recorder (per call: model, input, cached, output, unknown flag), turn and session totals, pure cost function; tests incl. missing usage, failed turn still billed, reset
- [x] 3.2 Fill `[ui.pricing."gpt-4.1"]` from OpenAI's published pricing page with `priced_on` and `source_url` (ask the user to confirm the figures; leave unpriced if they cannot be verified)
- [x] 3.3 Stream `usage` after every turn (including errors); `features/chat/UsageMeter` pill + breakdown popover with estimate/unpriced/lower-bound labels and `priced_on`
- [x] 3.4 Gates

## 4. MVP 4 — Scope guardrail

- [x] 4.1 Prompts: `prompts/scope_classifier.md`, `prompts/scope_redirect_fallback.md`, `prompts/scope_addendum.md` (XML structure, no tool names); prompt tests in `tests/prompts/`
- [x] 4.2 `agent/guardrails.py`: `ScopeGuard`, `ScopeVerdict`, classifier node (structured output with raw usage), routing; `build_agent(scope_guard=...)` with default graph unchanged
- [x] 4.3 `tests/agent/test_guardrails.py` with a fake chat model: domain query, methodology question, greeting and context-aware follow-up pass to the agent; coding/recipe/sports/politics requests get the redirect with the agent model never invoked and no tool run; malformed verdict fails open with a warning; blank reply uses fallback text; CLI prompt byte-identical
- [x] 4.4 `agent_runner` enables the guard and the addendum, emits `scope` and `guardrail_pivot`, counts classifier usage; frontend renders the pivot as a normal assistant message
- [x] 4.5 Gates

## 5. MVP 5 — Workspace state + overview ribbon

- [x] 5.1 `api/services/state_serializer.py`: pairing of tool calls with results, strict payload models, projector table keyed by tool name (test: every key is a registered tool)
- [x] 5.2 `api/services/projectors/`: inventory (facilities, coordinate checks), industry (by doc control number), NEI and SCC stacks with tiers, SCC lookup context, chemical properties, read-across, meteorology, population (coordinate tolerance), exposure (exactly-one emission-rate match); unattributed and warning lists
- [x] 5.3 Summary: max worst-case/representative HQ and cancer risk with facility/stack and status from thresholds; selected facility receptors; bounding box and framing version
- [x] 5.4 Tests for every spec scenario incl. malformed JSON, bad coordinates, ambiguous exposure, out-of-domain surrogate, "not yet computed", framing version unchanged on unrelated update
- [x] 5.5 Stream `workspace_update` after each tool batch; regenerate contract
- [x] 5.6 `hooks/useWorkspaceStore`; `components/ui/{StatusPill,SegmentedBar}`; `features/overview/{EpaOverviewRibbon,RiskMetricCard,ReadAcrossCard,DemographicsCard,MeteorologyCard}`; scientific notation and "not reported" formatting helpers (Vitest)
- [x] 5.7 Gates

## 6. MVP 6 — Facility map

- [x] 6.1 `features/map/ExposureMapCanvas` with light/dark styles from config and attribution; `FacilityMarker` layer coloured by status and sized by emission rate, legend
- [x] 6.2 `fitBounds` on framing-version change (instant under reduced motion); blank-canvas notice when tiles fail
- [x] 6.3 `api/services/geometry.py` buffer circle and schematic downwind sector GeoJSON (`(dir + 180) % 360`, configured half-angle) in `WorkspaceState` with pytest for bearings (270° → 90°); `features/map/PlumeSectorLayer` renders them labelled schematic
- [x] 6.4 Gates

## 7. MVP 7 — Facility inspector popover

- [x] 7.1 Focusable marker proxies with accessible names; glass `FacilityHoverCard` anchored via `map.project`, open on hover/focus, close on leave/blur/Escape
- [x] 7.2 Card content: header IDs and NAICS, emissions and schedule, every stack with tier pill, receptor metrics (worst-case and representative concentration, HQ, cancer risk, population); `api/routers/v1_facilities.py` `GET /api/v1/facilities/{frs_id}?thread_id=` returns the facility from the thread's state (404 when absent)
- [x] 7.3 Vitest: keyboard focus opens and Escape closes; three NEI stacks listed; absent values show "not reported"; pytest for the facilities route; Gates

## 8. MVP 8 — Polish and release

- [x] 8.1 HIG pass: spring transitions, blur fallback, dark mode across panes, reduced motion, WCAG AA contrast check, narrow-viewport stacked layout with segmented control
- [x] 8.2 README: build and launch, key setup, what the workspace does and does not show (schematic sector, three stack tiers, doc control number, no queried-chemical name)
- [x] 8.3 Full gates via `uv run pre-commit run --all-files`
- [x] 8.4 Manual end-to-end check in the browser with a real key (needs the user's go-ahead): save the key in Settings, a suggestion chip, streamed answer, pills, ribbon, map fit, inspector, usage meter, off-topic redirect
- [ ] 8.5 Ask the user before running `uv run pytest -m eval` once to confirm the CLI/eval path is unchanged (costs tokens)

## 9. Service keys (Census, CompTox) through Settings

Added at the user's request while MVP 4 was in progress; done before MVP 4's remaining tasks
because it changes the key vault, the turn runner and the settings sheet that those tasks build on.

- [x] 9.1 `[ui.keyring.accounts]` (openai, census, comptox) in settings and `config/ui.py` with tests; keep the OpenAI names as shipped
- [x] 9.2 `app/key_vault.py`: `ServiceKeys` (three vaults by name) and `default_service_keys()`; tests that keys are independent and use their own accounts
- [x] 9.3 `tools/credentials.py`: `CENSUS_KEY` and `COMPTOX_KEY`; population tool and CompTox client resolve their key per call (holder, then environment); tests incl. request key preferred, environment fallback, key not retained, and the existing missing-key behaviour
- [x] 9.4 Contract and routes: `KeysStatusResponse`; `census-key` and `comptox-key` routes and `GET /api/v1/settings/keys` from one route table; regenerate the contract; API tests for save/clear/status per key, independence, validation, no GET leaking any key (extend `test_security_keyring.py`)
- [x] 9.5 `agent_runner`: read the three keys once per turn, provide all three to tools for the turn, register stored values with the redaction filter for the turn; tests incl. tools seeing the right key, optional keys missing, concurrent turns, redaction of a Census key in a log record
- [x] 9.6 CLI: `app.run.ask` provides stored keys with environment fallback; tests
- [x] 9.7 Frontend: `useKeyStatus` for three keys, `ApiKeyVaultModal` with one section per key and a note on what is unavailable without the optional keys; tests (independent save/clear, no browser storage, optional-key notes)
- [x] 9.8 Update `api/CLAUDE.md`, `tools/CLAUDE.md`, `app/CLAUDE.md`, README; Gates

## 10. Inventory for the model and in bulk

Added at the user's request during the manual test (slow inventory; the model ranked 1,231
facilities by eye and got the top five wrong).

- [x] 10.1 FRS coordinates in one bulk request per `batch_size` IDs from the `dmapservice` best-pick lookup (`[frs_point]`), replacing one request per facility; reducer asks once; tests incl. batching, duplicates, one failed batch, rows for IDs not asked
- [x] 10.2 TRI window: last 2 published years (`recent_years = 2`, `publication_lag_years = 1`); tests
- [x] 10.3 Inventory tool tells the model the largest `[tri] max_listed` facilities (highest rate first) with `total_found`, `matching`, `shown`, `note`, optional `state` and `city`, and returns the complete list as an artifact; workspace reads the artifact; evals checks accept the new shape; tests
- [ ] 10.4 Re-record the inventory output of the evaluation cassette (it still holds the old list shape; replay works but does not exercise the new contract) — needs the live services and a model run, so only with the user's go-ahead
- [x] 10.5 Provider failures explained: `api/services/provider_errors.py` maps no credits, rejected key, rate limit, unreachable and server errors to fixed messages (the provider package is not imported); the scope check logs a provider refusal without a traceback; tests
- [x] 10.6 No part of any key is shown: the status of every key (OpenAI, Census, CompTox) is only `configured` (the masked last-four hint is removed from the vault, API, contract and Settings sheet); log redaction also covers the provider's masked-key echo (`sk-proj-****p8UA`), bearer tokens, key-like assignments and `?key=` URL query strings; keys from the environment (`.env`) are protected for the life of the server; tests
- [x] 10.7 Map actually draws: point MapLibre at its bundled worker (`setWorkerUrl`; the default URL 404s once Vite bundles the app, so nothing rendered); the camera fit keeps clear of the legend; the map starts on the contiguous US (`[ui.map.initial_view]`, sent in the client config); map errors logged to the console; verified in headless Chrome against the dev page and the production build
