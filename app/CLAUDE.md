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
- `key_vault.py` is the only module that touches the OS credential store (`keyring`), for the
  OpenAI, Census and CompTox keys (`ServiceKeys`, one entry each from `[ui.keyring]`). A key
  leaves it only as a `SecretStr`: the OpenAI one to `build_chat_model(..., api_key=...)`, all
  of them to the tools through `run.stored_keys_provided`. The program uses the stored keys and
  falls back to each key's environment variable for headless runs. `app` never imports `api`.
