# models/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `models/`.

- `models/` must not import langchain, langgraph, `tools`, `agent`, or `prompts`, and
  must not do I/O. Functions are pure and deterministic; validate inputs with `ValueError`.
- State units explicitly (e.g. g/s, mg/m^3, mg/(kg*day)) in every docstring.
