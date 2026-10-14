## Why

`fetch_chemical_properties` is the first step of every assessment, but property sources
(EPA, PubChem, etc.) are keyed on structure, not on the CAS numbers users give us. We need a
reliable CAS -> canonical SMILES step first, and the endpoint details must not be hard-coded
so they can change without code edits.

## What Changes

- Add a SMILES lookup helper under `tools/informatics/helpers/` that resolves a CAS number
  to a canonical SMILES via the PubChem PUG REST API and canonicalizes it with RDKit.
  Modelled on `GNN4EoL/src/data_engineering/extract/smiles_extractor.py` (CAS normalization,
  in-memory cache, PubChem property fallbacks, RDKit canonicalization), minus the pandas
  and singleton parts.
- Add a root-level `config/` package: a settings file holding the PubChem base URL,
  endpoint path template, request delay and timeout, plus a typed loader. No URL or endpoint
  string appears in Python code.
- Add `rdkit` and `httpx` as runtime dependencies.
- Document the new `config/` package and its dependency direction in `CLAUDE.md`.
- Tests live in `tests/tools/informatics/helpers/` (mirroring the package) and
  `tests/config/`; no network calls in the test suite.

Assumption: the request says the helper goes in "helpers folder inside tests/tools/informatics/".
Because it is production code, it is placed at `tools/informatics/helpers/` and only its tests
go under `tests/tools/informatics/helpers/`, per the layout rules in `CLAUDE.md`.

## Capabilities

### New Capabilities
- `smiles-lookup`: Resolve a CAS registry number to a canonical SMILES using PubChem and RDKit.
- `app-configuration`: Load external-service settings (URLs, endpoints, timing) from a
  configuration file through a typed loader instead of hard-coding them.

### Modified Capabilities

## Impact

- New code: `config/`, `tools/informatics/helpers/`, matching tests.
- `pyproject.toml` / `uv.lock`: new deps `rdkit`, `httpx`.
- `CLAUDE.md`: new `config/` entry; `tools` may import `config`.
- `fetch_chemical_properties` stays a stub; wiring the helper into it is a later change.
- Runtime makes outbound HTTPS calls to PubChem (tests mock them).
