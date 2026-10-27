## Why

Today an assessment run is a black box: the chat shows the answer and a cost figure, but not
which model calls and tool calls produced it, how long each took, or what a whole session cost.
To evaluate and debug the agent we need every run recorded as a trace on a monitoring platform
(Logfire, as in the course), with per-session cost. We also want those traces readable inside the
app, in the rail's Monitoring entry, which is a "Coming soon" placeholder today.

## What Changes

- Add Logfire as the monitoring platform. When the program starts (CLI and web server), it
  configures Logfire. Every agent run records one session trace, with every model call
  (prompt, completion, token usage) and every tool call (name, arguments, result, duration)
  nested under it. Traces are sent only when a Logfire write token is present, so tests and CI
  never send anything. `agent/` and the tools are unchanged.
- Add per-session cost tracking that reuses the existing usage meter (no second price table).
  Each session trace carries its calls, input, cached input and output tokens, estimated cost
  and cost status. The CLI prints a cost summary after the answer, as the course's
  `cost_tracker.py` does. In the web app, a session is the conversation thread: each turn is a
  trace tagged with the thread id and carries both the turn's and the running session's totals.
- Read the Logfire read token from the environment (`LOGFIRE_READ_TOKEN` in `.env`, as the
  course's `otel_test.py` does). The user is never asked to enter it, and it is redacted like
  the other environment keys.
- Add read-only monitoring endpoints that read traces back from the Logfire query API (as the
  course's `otel_test.py` does): recent sessions, and one session's ordered model and tool
  calls.
- Turn the Monitoring rail entry into a working view: a sessions table (time, question, model,
  model calls, tool calls, tokens, estimated cost, duration, status). Opening a session shows
  its timeline of model and tool calls, with a link to the trace in Logfire. When the server
  has no read token, or Logfire cannot be reached, the view says so and shows no invented data.
- Move the provider-neutral parts of the usage meter (call recording and cost estimation) from
  `api/` to `app/`, so the CLI and the web server use the same code.

## Capabilities

### New Capabilities
- `agent-telemetry`: Logfire setup at the program edge; the session/turn trace, with model and
  tool spans nested under it; the attributes each trace carries (session id, model, usage,
  cost); never sending without a token; no secrets in spans.
- `monitoring-dashboard`: the monitoring endpoints backed by the Logfire query API, the read
  token taken from the environment and never exposed, and the Monitoring view (sessions table,
  session timeline, link to Logfire, the not-configured and unavailable states).

### Modified Capabilities
- `usage-cost-meter`: per-session cost is also reported for command-line runs (printed summary)
  and attached to each run's trace.
- `web-ui-shell`: the Navigation rail requirement is replaced. "Monitoring" is enabled and
  opens the Monitoring view instead of being shown disabled with "Coming soon". The Settings
  drawer is unchanged.

## Impact

- **Dependencies**: `logfire` (already added on branch `add-logfire-monitoring`); `langsmith`,
  already installed, is used only as the OpenTelemetry bridge for LangChain runs (no LangSmith
  account, nothing sent to LangSmith).
- **Code**: new `config/telemetry.py` with a `[telemetry]` section in `settings.toml`; new
  `app/telemetry.py` and `app/usage_meter.py`; `app/run.py`, `app/__main__.py`,
  `api/__main__.py` and `api/services/agent_runner.py` wired to it; new
  `api/services/monitoring/`, `api/routers/v1_monitoring.py` and contract schemas;
  `.env.example` gains `LOGFIRE_TOKEN`/`LOGFIRE_READ_TOKEN`; frontend gets a Monitoring view
  and rail changes. The key vault, Settings drawer and the Overview, Map and Chat panels are not
  changed.
- **Data leaving the machine**: when a write token is configured, prompts, tool arguments and
  tool results (chemical identifiers, facility data, the user's questions) are sent to Logfire.
  API keys are never sent: they stay out of tool arguments, and scrubbing is on.
- **Setup (once, by whoever installs it)**: put a write token (`LOGFIRE_TOKEN`) and a read
  token (`LOGFIRE_READ_TOKEN`) from the Logfire project in `.env`, or run `logfire projects use`
  for the write side. App users never handle these tokens.
