# models/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `models/`.

- `models/` must not import langchain, langgraph, `tools`, `agent`, or `prompts`, and
  must not do I/O. Functions are pure and deterministic; validate inputs with `ValueError`.
- State units explicitly (e.g. g/s, mg/m^3, mg/(kg*day)) in every docstring.
- Group modules in subfolders by what they model: `transport/` (dispersion, plume rise,
  wind profile, screening search), `weather/`, `receptors/`, `exposure/` (dose, inhalation,
  risk), `chemistry/` (read-across similarity). Shared type aliases stay in `_types.py`. Add
  a new module to the folder it belongs to, or a new folder (with its `__init__.py`) when
  none fits; mirror it under `tests/models/`.
