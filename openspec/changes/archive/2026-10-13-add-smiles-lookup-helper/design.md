## Context

Layout rules in `CLAUDE.md`: `tools/` holds tool logic and must not call an LLM or import
from `agent/`; `models/` is pure; Python files need `from __future__ import annotations`;
pyright is strict. The reference implementation (`smiles_extractor.py`) is a pandas-aware
singleton that reads a global `ConfigManager`. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- A small, testable CAS -> canonical SMILES function/class with no hidden global state.
- All PubChem URL/endpoint/timing values come from a config file.

**Non-Goals:**
- Wiring into `fetch_chemical_properties` or registering a new `@tool` (later change).
- Name or InChI lookups, batch/DataFrame processing, persistent (on-disk) caching.
- Fetching molecular properties themselves.

## Decisions

1. **Location: `tools/informatics/helpers/smiles.py`** (tests in `tests/tools/informatics/helpers/`).
   The request mentioned a helpers folder under `tests/`; production code there would break
   the mirrored-test-layout rule. Helpers are plain functions/classes, not `@tool`s, so the
   tool-registry rules do not apply; they stay inside the informatics group so no tool
   imports another tool subfolder.
2. **Root-level `config/` package** with `settings.toml` and `loader.py`. A new top-level
   package is needed because both `tools` and potentially `agent` consume it, and it cannot
   live inside `models/` (no I/O). Dependency direction becomes `agent`/`tools` -> `config`;
   `config` imports nothing from the project. `CLAUDE.md` is updated.
3. **TOML via stdlib `tomllib`** over YAML/JSON: no new dependency, comments allowed,
   Python 3.13 guarantees availability. Settings are returned as frozen dataclasses
   (`PubChemSettings`) and validated with `ValueError`, matching the `models/` convention.
   `get_settings()` is `lru_cache`d; `load_settings(path)` takes an explicit path for tests.
4. **Endpoint as template:** config stores `base_url` plus
   `compound_property_path = "/compound/name/{identifier}/property/CanonicalSMILES/JSON"`.
   The helper formats the identifier with `urllib.parse.quote`. PubChem resolves CAS numbers
   as compound-name synonyms, as in the reference.
5. **HTTP client: `httpx`** over `requests`: ships type hints (clean under strict pyright)
   and `MockTransport` enables network-free tests. The client is injectable
   (`SmilesLookup(settings, client=None)`), the delay via an injectable `sleep` callable.
6. **Class `SmilesLookup` instead of a singleton:** holds the cache; callers share one
   instance. Avoids global state that makes tests order-dependent. The cache stores
   definitive outcomes only (a found SMILES, or a 404 miss); network errors and timeouts are
   not cached so they can be retried.
7. **RDKit is a hard dependency** (the reference's optional-import fallback is dropped);
   a missing install fails fast at import. RDKit stub typing is incomplete under pyright
   strict, so use targeted `# pyright: ignore[...]` with reasons, or a small typed wrapper.

## Risks / Trade-offs

- [PubChem rate limit (~5 req/s) / outages] -> configurable delay; failures return None, not raise.
- [`rdkit` wheel size / platform support] -> pinned via uv lock; verify `uv sync` on target platforms.
- [PubChem response field names change (`CanonicalSMILES` vs `SMILES`)] -> fallback list, and
  the property name lives in the endpoint template config.
- [CAS name lookup may return a wrong compound for ambiguous synonyms] -> accepted for
  screening-level use; the caller sees only the SMILES, so surface this in docstrings.
- [Silent `None` on failure hides causes] -> debug logging of status/exception.
