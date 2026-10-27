## Context

See proposal.md for the motivation. Constraints that shape the approach:

- The agent is LangGraph/LangChain. The course's `logfire.instrument_pydantic_ai()` does not
  apply here, and `agent/` must stay provider-agnostic and free of monitoring code
  (`agent/CLAUDE.md`).
- `app/` and `api/` are the outer edges. `app` never imports `api`; `api` may import `app`.
- A usage meter already exists (`api/services/usage_meter.py`: `UsageRecorder`, `CallUsage`,
  `estimate_cost`, `summarize`, priced from `[ui.pricing]`). The web UI already shows turn and
  session cost. The CLI shows none.
- User-facing keys (OpenAI, Census, CompTox) live in the OS keychain. Environment keys from
  `.env` are protected from logs by `api/main._environment_keys` → `protect_secrets`. The Logfire
  tokens are installation settings, not user keys, so they go in `.env` (user decision).
- A probe (scratch script, fake chat model plus one tool) confirmed the bridge used below. With
  Logfire configured, a `LangChainTracer` whose langsmith `Client` uses `tracing_mode="otel"`
  writes the LangGraph root, each chat model call (with `usage_metadata`) and each tool call
  (`gen_ai.tool.name`) as OpenTelemetry spans. It reuses Logfire's global tracer provider and
  puts them all in one trace, under the span that is current when the run starts.

## Goals / Non-Goals

**Goals:**
- Every CLI run and every web turn becomes one Logfire trace with nested model and tool spans.
- One meter and one price table for the CLI, the web UI and the trace attributes.
- A Monitoring view that only shows data read back from Logfire.

**Non-Goals:**
- No alerting, dashboards or saved queries inside Logfire itself (users can build those there).
- No offline or local trace store; without Logfire the view says so.
- No change to the eval harness's own Evidently reporting (evals may opt into tracing later).
- No metrics or log export other than spans.

## Decisions

### D1. LangChain → OpenTelemetry through LangSmith's OTel tracer, passed as a callback
`app/telemetry.py` builds `LangChainTracer(client=Client(tracing_mode="otel"))`. Callers add it
to the run configuration's `callbacks`, next to `UsageRecorder`.
- *Why*: it covers chains, model calls and tool calls with `gen_ai.*` attributes, nests under
  our span, and needs no new dependency (`langsmith` is already installed). Because it is an
  injected callback, no environment variable is set globally and `agent/` is unchanged.
- *Alternatives*: `logfire.instrument_openai()` sees only OpenAI HTTP calls, with no tool spans
  and no graph structure. Setting the `LANGSMITH_TRACING`/`LANGSMITH_OTEL_*` environment
  variables is a process-wide side effect that depends on import order, because langsmith
  caches environment lookups. The OpenInference LangChain instrumentor adds a dependency for the
  same result.
- The tracer is built only when monitoring is enabled. When it is disabled, no callback is
  added and runs are unchanged.

### D2. Session span opened by the caller; usage set on it at the end
`app/telemetry.py` exposes a context manager, `session_span(kind, session_id, question,
model)`, which yields a handle used to record the outcome and the usage totals. It uses the
span names and attribute names from `[telemetry]`. Attribute names follow OpenTelemetry where
one exists (`session.id`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, ...); the rest
are project-namespaced (`exposure.cost_usd`, `exposure.cost_status`,
`exposure.session.cost_usd`, ...). The CLI opens it around `agent.invoke` in `app/run.ask`. The
web server opens it in `run_turn`, with the thread id as `session.id`.
- *Why*: the session is a concept of the program, not of the agent. Setting usage at the end
  means the span reports the same numbers the meter shows, so the Monitoring view never has to
  re-price anything.

### D3. The provider-neutral meter moves to `app/usage_meter.py`
`CallUsage`, `UsageRecorder`, `Cost` and `estimate_cost` move to `app/`. `summarize` (which
builds the `UsageTotals` wire schema) stays in `api/services/usage_meter.py` and imports from
`app`. `api/services/threads.py` imports `CallUsage` from `app`. The tests move with the code.
- *Alternative*: duplicate a small cost accumulator in `app/` as the course does. Rejected:
  that would be two sources of truth for prices and cached-token handling.

### D4. CLI cost summary
`ask` returns the answer together with the run's `CallUsage` list. `app/__main__.py` prints the
answer on stdout and a summary on stderr (calls, token totals, `≈ $x.xxxx (estimate, prices of
YYYY-MM-DD)`, or "unpriced" / "lower bound"), so piping the answer stays clean. Formatting lives
in a small pure function so it can be tested.

### D5. Logfire setup: `configure_telemetry(settings)`
Called first thing in `app/__main__.main` and `api/__main__.main` (never at import, never in
tests). It calls `logfire.configure(service_name, environment, send_to_logfire=
"if-token-present", console=<setting>, scrubbing=ScrubbingOptions(extra_patterns=...))`. The
extra patterns are the key-shaped patterns that `api/core/logging_filter.py` already redacts,
moved to `config` or `commons`, so the logs and the spans share one list. The write token is
read by Logfire itself during `configure`: `LOGFIRE_TOKEN` from `.env` (loaded by `load_dotenv`
before `configure_telemetry`), or `.logfire/` from `logfire projects use`. `.logfire/` is added
to `.gitignore`.

### D6. Logfire read token from `.env`, read only by the monitoring service
`[telemetry].read_token_env_var = "LOGFIRE_READ_TOKEN"` names the variable, as `[agent]` does
for its key. The monitoring service reads it per request from an injected environment mapping
(tests pass a dict) and wraps it as a `SecretStr`. It is never put in `HOLDERS`, the run
configuration or any response. Its variable is added to `api/main._environment_keys`, so
`protect_secrets` redacts it from logs. The key vault, `KeyName` and the Settings drawer stay
unchanged.
- *Alternative considered*: a fourth keychain key edited in Settings. Rejected by the user: the
  token belongs to the installation, and app users should not be asked for it.

### D7. Monitoring backend: `api/services/monitoring/` and `api/routers/v1_monitoring.py`
- `GET /api/v1/monitoring/sessions` and `GET /api/v1/monitoring/sessions/{session_id}`.
  The response shapes are added to the wire contract (`api/schemas/monitoring.py`, included in
  the contract export so the frontend types stay generated).
- The query client is injected (`AsyncLogfireQueryClient`, built per request from the
  environment token with `[telemetry].query_timeout_seconds`) behind a small protocol, so tests
  use a fake.
- Queries are SQL over Logfire's `records` table: session spans by `span_name` within
  `min_timestamp`, then the child spans of the selected traces. They use `limit` and the
  configured window. The session id is matched against `^[A-Za-z0-9_-]{1,64}$` before it is put
  into SQL. The query API has no bind parameters, so this check is the injection guard. It is
  done once at the router boundary.
- Rows are untrusted: each field is checked for type and finiteness, and a bad field becomes
  absent with a logged warning (fail closed).
- Tool step names reuse `[ui.step_labels]`. The Logfire link comes from
  `[telemetry].trace_url_template`, filled with the organization and project from
  `client.info()` (cached per token for the process) and the trace id.
- Errors map to states: no token → `not_configured`; `QueryRequestError` with 401/403 →
  `unauthorized`; timeouts, rate limits and HTTP errors → `unavailable`. The details are logged
  through the existing redaction.

### D8. Frontend: a view switch in `App.tsx`, a new `features/monitoring/`
`App.tsx` holds `view: "workspace" | "monitoring"`. The rail's Monitoring item gets an
`onClick` and `current` like Workspace. The `SplitWorkspace` stays mounted and is hidden (not
unmounted) while Monitoring is shown, so the map and chat keep their state. The Overview, Map
and Chat components themselves are not modified. `features/monitoring/` holds
`MonitoringView`, `SessionsTable`, `SessionTimeline` and a `useMonitoring` hook calling the two
endpoints through the existing `services/` API client, reusing the dashboard's number and cost
formatters. The Settings drawer is not changed.

## Risks / Trade-offs

- [A span opened inside the async SSE generator may be closed in another context when the client
  disconnects, so OpenTelemetry logs "Failed to detach context".] → `run_turn` already drives
  the whole turn inside one generator iterated by one task. Add a test that closes the stream
  early and checks that the span ends with outcome `error` and nothing else is logged. If that
  fails, start the span manually (no context attach) and pass it as the explicit parent through
  langsmith's run metadata.
- [Prompts, tool results and user questions leave the machine when a write token is set.] →
  This is opt-in through the token, documented in the README, and scrubbed of key patterns.
  Users can set `[telemetry].enabled = false`.
- [Logfire's `records` schema or the langsmith OTel attribute names change between versions.] →
  The span and attribute names we write ourselves come from config. Queries read only those plus
  `span_name`/`trace_id`/timestamps, and smoke tests (`-m smoke`, skipped without a token) check
  a real round trip.
- [The langsmith `Client` may warn or try a network call without a LangSmith API key, even in
  otel mode.] → Verify in task 2.2. If it does, give it a dummy key that is documented as never
  sent (otel mode posts nothing to LangSmith) and test that no request reaches
  `api.smith.langchain.com`.
- [The tokens in `.env` are new secrets.] → `.env` is already gitignored and covered by
  detect-secrets. The read token is added to log redaction and span scrubbing, and a test checks
  that no monitoring response or log record contains it.
- [The Logfire query API rate-limits.] → A refresh is user-triggered only (no polling), and the
  list is one query per request.

## Migration Plan

1. Ship with `[telemetry].enabled = true` and `send_to_logfire="if-token-present"`. Without a
   token nothing changes for the user.
2. Installer setup, documented in README and `.env.example`: create a Logfire project, then put
   a write token in `LOGFIRE_TOKEN` and a read token in `LOGFIRE_READ_TOKEN` in `.env`
   (`logfire projects use` is an alternative for the write side). Restart the server.
3. Rollback: set `[telemetry].enabled = false`. The Monitoring view then shows no new sessions.
   Without `LOGFIRE_READ_TOKEN` it shows `not_configured`. No data migration.

## Open Questions

- The exact Logfire trace-link URL format for this account's region. It is a config template
  (`trace_url_template`), so it can be confirmed against the live UI during implementation
  without changing the specs or tasks.
