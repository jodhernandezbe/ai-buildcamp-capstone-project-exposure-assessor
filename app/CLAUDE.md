# app/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `app/`.

- The program's outer edge: build the configured chat model and run the agent. No domain
  logic (that is `tools/`) and no graph wiring (that is `agent/`).
- `chat_model.py` is the only module that imports a chat provider package (lazily, chosen by
  `[agent].provider`). The program and `evals/` both build the agent's model through it, so
  they always run the same model; never construct a chat model anywhere else.
- Model name, key variable, timeout and step limit come from `[agent]` in
  `config/settings.toml`; never hard-code them.
- Tests inject a fake environment or a fake chat model; never call a real provider.
