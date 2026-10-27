## 1. Setup and configuration

- [x] 1.1 Keep `logfire` in `pyproject.toml`/`uv.lock` (added on branch `add-logfire-monitoring`); add `.logfire/` to `.gitignore`; add commented `LOGFIRE_TOKEN` and `LOGFIRE_READ_TOKEN` placeholders to `.env.example`
- [x] 1.2 Add `[telemetry]` to `config/settings.toml` (enabled, service_name, environment, console, read_token_env_var, session/turn span names, attribute names, query_timeout_seconds, session_window_hours, max_sessions, trace_url_template) and `config/telemetry.py` typed loader with tests in `tests/config/test_telemetry_settings.py` (missing key, wrong type, bool-as-number, non-positive limits)

## 2. Telemetry in `app/`

- [x] 2.1 Move `CallUsage`, `UsageRecorder`, `Cost`, `estimate_cost` to `app/usage_meter.py`; keep `summarize` in `api/services/usage_meter.py` importing from `app`; update `api/services/threads.py`; move tests to `tests/app/test_usage_meter.py`
- [x] 2.2 Create `app/telemetry.py`: `configure_telemetry(settings)`, `run_tracer(settings)` (LangChainTracer with an otel-mode langsmith Client, or None when disabled), `session_span(...)` context manager and `record_usage(handle, calls, pricing, prefix)`; verify the langsmith Client needs no LangSmith key and makes no LangSmith request
- [x] 2.3 Share the key-shaped redaction patterns between log redaction and Logfire scrubbing (one list, in `config`/`commons`), with a test that a key in a tool result is scrubbed from spans
- [x] 2.4 Tests in `tests/app/test_telemetry.py` using `logfire.testing` capture (never sending): fake model + one tool gives session → model/tool spans in one trace; disabled → no spans; failed run → outcome `error`; usage attributes for priced, lower-bound and unpriced cases; no key in any span

## 3. Command-line program

- [x] 3.1 `app/run.py`: `ask` opens the session span (new session id), adds `UsageRecorder` and the tracer to the run callbacks, sets usage and outcome on the span, and returns the answer with its calls
- [x] 3.2 `app/__main__.py`: call `configure_telemetry` first, print the answer to stdout and the cost summary (pure formatter) to stderr; tests for the formatter (estimate, lower bound, unpriced) and for `main` with a fake model
- [x] 3.3 Update existing `tests/app/test_run.py` callers and any `evals/` use of `ask` for the new return shape

## 4. Web server telemetry

- [x] 4.1 `api/__main__.py`: call `configure_telemetry` after `load_dotenv` and before `uvicorn.run`; add `[telemetry].read_token_env_var` to `api/main._environment_keys` so the read token is redacted from logs
- [x] 4.2 `api/services/agent_runner.py`: open the turn span (session id = thread id, question, model) in `run_turn`, add the tracer to `_run_config` callbacks, set turn and session usage and outcome before `turn_finished`
- [x] 4.3 Tests: turn span carries the thread id and both turn/session totals; two turns share the session id; failed turn ends `error`; a stream closed early ends the span without context-detach errors

## 5. Monitoring backend

- [x] 5.1 Add `api/schemas/monitoring.py` (session summary, session detail, turn, step, state enum `ok|not_configured|unavailable|unauthorized`) and include them in the contract export; regenerate frontend types
- [x] 5.2 Create `api/services/monitoring/` with: a query-client protocol and the default `AsyncLogfireQueryClient` factory (token as `SecretStr` from the injected environment, configured timeout); the SQL builders for sessions and session detail (session-id regex check); row parsers that validate type/finiteness and turn bad fields into absent values with a warning; error → state mapping; trace link from the URL template and `client.info()`
- [x] 5.3 Create `api/routers/v1_monitoring.py` with `GET /api/v1/monitoring/sessions` and `GET /api/v1/monitoring/sessions/{session_id}` (422 on malformed id, 404 on unknown id); register it in `api/main.py`
- [x] 5.4 Tests with a fake query client: listing order and fields; missing cost attribute → absent/unknown; no token → `not_configured` and no call; timeout/rate limit → `unavailable`; 401 → `unauthorized`; malformed id → 422 without a query; unknown id → 404; the read token never appears in a response or log record, including on Logfire errors
- [x] 5.5 Smoke test (`-m smoke`, skipped without `LOGFIRE_READ_TOKEN`) listing real sessions

## 6. Frontend

- [x] 6.1 `LeftNavRail.tsx`: enable Monitoring with `onClick` and current-page marking; update `LeftNavRail.test.tsx` (remove "Coming soon" expectations, add current-page and activation tests)
- [x] 6.2 `App.tsx`: `view` state; keep `SplitWorkspace` mounted but hidden while Monitoring is shown; Workspace returns to it; Monitoring closes Settings and dialogs
- [x] 6.3 Create `features/monitoring/` (`MonitoringView`, `SessionsTable`, `SessionTimeline`, `useMonitoring`) using the existing API client and formatters; states: loading, ok, empty window, not_configured (explains, no token input), unavailable/unauthorized (retry)
- [x] 6.4 Frontend tests for each state, session selection, "Open in Logfire" link (`target="_blank"`, `rel="noopener noreferrer"`), and returning to the workspace with panels unchanged; `npm --prefix frontend run check`

## 7. Docs and verification

- [x] 7.1 README: monitoring setup (`LOGFIRE_TOKEN` and `LOGFIRE_READ_TOKEN` in `.env`, or `logfire projects use`), what is sent, how to turn it off; update `app/CLAUDE.md` and `api/CLAUDE.md` for telemetry and the read token
- [x] 7.2 Run the full gate: `uv run pre-commit run --all-files` (pytest, ruff, pyright, bandit, function length, frontend check)
- [x] 7.3 Manual check: `uv run python -m app "Assess CAS 71-43-2"` with a write token; confirm the trace in Logfire (session span, model calls with tokens, tool calls) and the printed cost summary; then open Monitoring in the web UI and confirm the same session appears with matching tokens and cost
