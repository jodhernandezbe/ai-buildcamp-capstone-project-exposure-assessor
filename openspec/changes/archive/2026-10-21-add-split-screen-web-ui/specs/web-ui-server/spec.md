## Purpose

The local web program that serves the split-screen interface and runs the exposure assessor
agent for each chat turn, streaming its progress to the browser as typed events.

## ADDED Requirements

### Requirement: Single-command local launch
The system SHALL start the web program with one command that serves both the API and the
built frontend from the same origin. It SHALL bind only to the loopback interface on the host
and port read from configuration, and SHALL refuse to start with a clear message when the
built frontend is missing.

#### Scenario: Launch
- **WHEN** the user runs the launch command after building the frontend
- **THEN** the interface is served at the configured loopback address and the API answers under `/api`

#### Scenario: Frontend not built
- **WHEN** the launch command runs and the built frontend directory does not exist
- **THEN** the program exits with a message naming the build command, and no server starts

#### Scenario: Non-loopback host configured
- **WHEN** the configured host is not a loopback address
- **THEN** loading the configuration raises an error naming the host key

### Requirement: Cross-site requests are rejected
Every state-changing endpoint (chat turns, saving or clearing the key, resetting a thread)
SHALL reject requests whose `Origin` (or, without one, `Referer`) is not the program's own
origin, and SHALL reject requests whose `Host` is not the configured loopback host and port,
so a third-party web page cannot spend tokens or change the key.

#### Scenario: Foreign origin
- **WHEN** a `POST` to the chat endpoint carries `Origin: https://example.com`
- **THEN** the response is 403 and the agent is not run

#### Scenario: Same origin
- **WHEN** a `POST` carries the program's own origin
- **THEN** the request is processed

#### Scenario: DNS-rebinding host
- **WHEN** a request arrives with a `Host` header other than the configured host and port
- **THEN** the response is 403

### Requirement: Chat turn streaming
A chat turn SHALL be submitted as a `POST` to the versioned chat-stream endpoint with a thread identifier and the user's message, and
SHALL be answered with a `text/event-stream` of JSON events, each with a `type` and a monotonically
increasing `seq`, in this vocabulary:
- `turn_started` (thread id, turn id);
- `scope` (in or out of scope);
- `guardrail_pivot` (the in-character redirect text, when out of scope);
- `tool_status` with phase `started` (call id, tool name, human-readable step label) or
  `finished` (call id, status `ok` or `error`, short summary), never including raw tool payloads;
- `workspace_update` (the full current workspace state of the thread);
- `token` (assistant text fragment) and `assistant_message` (final text);
- `usage` (this turn's and the session's token and cost totals);
- `error` (a user-safe message and a correlation id);
- `turn_finished`.
The stream SHALL always end with `turn_finished`, including after an error.

#### Scenario: In-scope turn with tools
- **WHEN** a turn makes two tool calls and then answers
- **THEN** the stream contains `turn_started`, `scope`, a started/finished `tool_status` pair per call, at least one `workspace_update`, the assistant text, `usage` and `turn_finished`, in `seq` order

#### Scenario: Agent failure mid-turn
- **WHEN** the chat model raises during a turn
- **THEN** the stream emits `error` with a generic message and a correlation id, then `turn_finished`

#### Scenario: Provider has no credits
- **WHEN** the model provider refuses a turn because the account has no credits left
- **THEN** the stream emits `error` saying so plainly and pointing to the provider's billing, with a correlation id, then `turn_finished`; the provider's own text is not shown

#### Scenario: Other provider failures
- **WHEN** the provider rejects the key, rate-limits the request, cannot be reached or reports a server error
- **THEN** the `error` message says which of these happened and what to do, from a fixed set of messages

#### Scenario: No key configured
- **WHEN** a chat turn is submitted and no key is stored
- **THEN** the stream emits `error` saying the key must be set in Settings, then `turn_finished`, and no model is built

### Requirement: One wire contract between frontend and backend
The frontend SHALL interact with the system only through the backend's HTTP API and event
stream; it SHALL NOT call the agent, the tools or external assessment services directly (only
basemap tiles are fetched by the browser). Every request body, response body, event and the
dashboard state SHALL have one schema, published by the backend as a machine-readable
document; the frontend's types SHALL be generated from that document, and a check SHALL fail
when the generated types are out of date. The agent and its tools SHALL NOT depend on the
backend or the frontend.

#### Scenario: Contract drift
- **WHEN** an event field is renamed in the backend schema and the frontend types are not regenerated
- **THEN** the contract check fails

#### Scenario: Agent independent of the web
- **WHEN** the command-line program runs
- **THEN** no backend or frontend module is imported

### Requirement: Step labels are human-readable
Each started `tool_status` event SHALL carry a short label for the step, looked up by tool name from
configuration (e.g. the emissions inventory tool reads as "Queried EPA TRI releases"), falling
back to the tool name when no label is configured.

#### Scenario: Configured label
- **WHEN** the emissions inventory tool starts
- **THEN** its event label is the configured text, not the function name

#### Scenario: Unlabelled tool
- **WHEN** a tool without a configured label starts
- **THEN** its label is the tool name

### Requirement: Conversation threads
The program SHALL keep each thread's message history and dashboard state in process memory so
follow-up turns see earlier turns, SHALL allow a thread to be reset, and SHALL NOT persist
threads to disk. Only one turn per thread SHALL run at a time.

#### Scenario: Follow-up turn
- **WHEN** a second turn is sent on the same thread
- **THEN** the agent receives the first turn's messages and the dashboard keeps the earlier facilities

#### Scenario: Reset
- **WHEN** the thread is reset
- **THEN** its history, dashboard and session usage are cleared

#### Scenario: Concurrent turn on one thread
- **WHEN** a turn is submitted while another turn of the same thread is still running
- **THEN** the second request is answered 409 and the running turn is unaffected

### Requirement: Leak-free errors
Error responses and error events SHALL contain only a message and a correlation id; the message is generic, or one of a fixed set of plain-language messages for known provider failures (no credits, rejected key, rate limit, unreachable, server error) and for a missing key or keychain. It is never the provider's or the exception's own text.
They SHALL NOT include exception text, tracebacks, request headers, request bodies or any
key material; the details SHALL go only to the (redacted) server log under the same
correlation id.

#### Scenario: Unhandled exception
- **WHEN** an endpoint raises an exception whose message contains `sk-` followed by a key
- **THEN** the HTTP response body contains neither the exception text nor the key, and the server log entry is redacted

#### Scenario: Validation error
- **WHEN** a request body fails validation
- **THEN** the response names the invalid field but does not echo submitted values
