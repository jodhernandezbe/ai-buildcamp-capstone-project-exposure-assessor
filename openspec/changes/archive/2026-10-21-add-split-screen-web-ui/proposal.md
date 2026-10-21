## Why

The exposure assessor is only reachable from a one-shot CLI (`python -m app "..."`), so an
assessment is a wall of Markdown with no view of where the facilities are, which inputs were
generic, or what a run cost. A local, single-command web app that pairs a live dashboard and
facility map with a conversational copilot makes the agent's evidence visible as it is
gathered, keeps the OpenAI key out of files, and keeps the conversation on its scientific
mission.

## What Changes

- Three separated layers with one-way dependencies: `frontend/` (browser app) talks to
  `api/` only over HTTP + SSE; `api/` drives the existing agent core (`app/` -> `agent/`
  -> `tools/` -> `models/`) in-process; the agent core never imports `api/` and knows nothing
  about the web. The wire contract (event and state schemas) is defined once in `api/` and
  the frontend's TypeScript types are generated from it.
- New local web backend `api/` (FastAPI, Router → Service → Domain, thin adapter over the agent; launched with `uv run python -m api`, bound to
  `127.0.0.1`) that runs the existing LangGraph agent per chat turn and streams typed events
  (assistant text, tool-step pills, dashboard updates, token usage) to the browser over SSE.
- New frontend `frontend/` (React + TypeScript + Vite + Tailwind + MapLibre GL + Recharts +
  Lucide), built once and served as static files by the same server. Locked `100dvh` x
  `100dvw` split screen following Apple HIG materials and motion:
  - Left (~63%): executive summary ribbon (HQ / cancer risk, chemical & read-across provenance,
    exposed population with age bands, meteorology pill) over an interactive facility map with
    `flyTo` fitting, buffer circle, schematic downwind sector, and a glass hover/focus inspector
    per facility.
  - Right (~37%): copilot chat with onboarding suggestion chips, collapsible tool-step pills,
    a token & cost meter, and a top-right gear that opens the API-key settings sheet.
- The dashboard only shows values a tool actually returned; anything not reported renders as
  absent with a reason (no invented or derived-by-the-UI numbers).
- OpenAI key stored only in the OS credential store via `keyring` (service
  `epa-chemical-risk-agent`, account `openai_api_key`, both from config), read fresh for each
  request and passed as `SecretStr` to the one chat-model factory. The same key drives the
  scope classifier and the agent. `GET` endpoints only ever return `configured` + a masked hint.
- `SecretRedactionFilter` on the root, `uvicorn*` and `httpx` loggers scrubs
  `sk-[A-Za-z0-9_-]{10,}`; exception handlers return generic messages with no headers or keys.
- New `agent/guardrails.py`: an opt-in scope node that asks the injected chat model for a
  structured in/out-of-scope verdict on the latest user turn; off-topic turns get a warm,
  in-character redirect and never reach the tool-bound model. The web UI enables it and adds a
  scope addendum to its system prompt; the CLI and evals keep today's graph and prompt
  byte-identical.
- Token consumption and money spent: per-turn and per-session input / cached / output tokens
  from every model call (classifier included) and an estimated USD cost from per-model prices
  in `config/settings.toml`; unpriced models show tokens with cost marked "unpriced".
- `build_agent` gains optional `scope_guard` and `checkpointer` parameters (defaults keep the
  current behaviour). `app/` gains a key vault and a chat-model factory that accepts an
  injected key; the CLI reads the vault first and falls back to `OPENAI_API_KEY` so evals/CI
  still run headless.

## Capabilities

### New Capabilities
- `web-ui-server`: the local FastAPI program: launch command, localhost binding and origin
  checks, chat turn streaming over SSE with a typed event contract, in-memory conversation
  threads, static frontend serving, leak-free error handling.
- `api-key-vault`: keyring-backed save / status / clear of the OpenAI key, per-request
  retrieval, masked status endpoint, and the log redaction filter.
- `scope-guardrail`: the opt-in agent scope classifier and polite redirect, and the UI scope
  addendum prompt.
- `assessment-dashboard-state`: pure projection of tool calls and results into the typed
  dashboard state (summary ribbon, facilities, stacks, receptors, meteorology, chemical
  provenance), failing closed on anything unverified or unattributable.
- `usage-cost-meter`: token accounting per model call, per turn and per session, and USD cost
  estimation from configured prices.
- `web-ui-shell`: the split-screen frontend: layout, materials, motion, summary ribbon, facility
  map and inspector, chat, onboarding chips, tool pills, settings sheet and usage meter.

### Modified Capabilities
- `app-configuration`: the agent chat model can be built from an injected key (vault) as well
  as the environment variable; new `[ui]` settings table (server, keyring names, prompts,
  map styles, display thresholds, pricing).

## Impact

- New packages/dirs: `api/` (Python layer) with `api/CLAUDE.md`, `frontend/` (Node/Vite
  project; `dist/` and `node_modules/` git-ignored) with `frontend/CLAUDE.md`, `tests/api/`, `prompts/scope_classifier.md`, `prompts/scope_addendum.md`.
- Modified: `agent/graph.py` (optional guard + checkpointer), new `agent/guardrails.py`,
  `app/chat_model.py` (injected `SecretStr`), new `app/key_vault.py`, `app/__main__.py` / `app/run.py`
  (vault-then-env key), `config/settings.toml` + new `config/ui.py`, root `CLAUDE.md` (layer +
  dependency direction), `.pre-commit-config.yaml` / bandit / function-length target lists,
  `.gitignore`, `README.md`.
- New dependencies: `fastapi`, `keyring` (Python); React, Vite, Tailwind, MapLibre GL, Recharts,
  Lucide, Vitest (npm, dev-only toolchain; Node is needed only to build the frontend).
- External services at runtime: Carto basemap tiles (browser) in addition to the existing
  agent services. No change to tool behaviour, tool descriptions, `prompts/agent_system.md`,
  or eval scenarios.
