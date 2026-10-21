# api/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `api/`.

- A thin HTTP/SSE transport, security and state-serialisation adapter over the agent core.
  Never duplicate physics, EPA queries or read-across math here; those live in `tools/` and
  `models/`. If the UI needs a new fact, it needs a tool, not an `api/` function.
- Layering: `routers/` (thin handlers, no logic) -> `services/` (orchestration: agent runner,
  state serializer, threads, usage) -> the agent core. `core/` holds config view, keyring,
  log redaction and exception handlers; `schemas/` holds every wire model.
- Allowed imports: `app`, `agent`, `config`, `commons`, `prompts`, `tools.schemas` (types
  only) and `tools.credentials` (to give the turn's keys to the tools that need them). Never import tool modules, provider packages or `evals`; nothing imports `api`.
- Settings come from `[ui]` in `config/settings.toml` via `config.ui`; `api/core/config.py`
  only exposes them to `Depends()`. Never read ports, origins or names from the environment.
- The chat model is built only through `app.chat_model`. The OpenAI, Census and CompTox keys
  are read once per turn from `app.key_vault.ServiceKeys`, given to the tools through
  `tools.credentials.HOLDERS` for that turn only, protected from the logs, and never stored on
  anything that outlives the turn. Only the OpenAI key is required.
- `api/schemas/` is the single wire contract with `frontend/`. After changing it run
  `uv run python -m scripts.export_contract` and `npm --prefix frontend run gen:types`.
- Responses, events and logs never contain exception text, request headers or key material;
  log through the redaction filter and return a generic message with a correlation id.
- The workspace shows only what tools returned: never compute, estimate or convert values
  (geometry for drawing the buffer and schematic sector is the one exception); anything
  unverified or unattributable becomes absent with a reason.
- Tests mirror the layout under `tests/api/`; they inject a fake vault, a fake chat model and
  an in-memory keyring backend and never touch the real keychain or a real provider.
