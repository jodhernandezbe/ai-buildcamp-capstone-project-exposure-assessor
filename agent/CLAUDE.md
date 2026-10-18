# agent/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `agent/`.

- `agent/` must stay provider-agnostic: accept a `BaseChatModel` by injection.
  Never import `langchain_openai`, `langchain_anthropic`, etc. in `agent/`, `tools/`,
  or `prompts/` (sole exception: the embeddings factory in
  `tools/emissions/rag/embeddings.py`, see `tools/CLAUDE.md`).
- Do not put domain or calculation logic in `agent/`. If the agent needs a
  capability, add a tool.
- The agent reads tools only via `tools.registry`.
