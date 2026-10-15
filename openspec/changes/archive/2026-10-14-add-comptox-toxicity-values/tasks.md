## 1. Configuration

- [x] 1.1 Add `toxval_by_dtxsid_path`, `source_priority` and `[[comptox.toxicity_values]]` (rfd, rfc, sf with labels SF and OSF, iur) to `config/settings.toml`
- [x] 1.2 Add `ToxicityValueSpec` and extend `ComptoxSettings` / `load_comptox_settings` in `config/loader.py` (URL property, `{dtxsid}` placeholder check, source list of strings, non-empty `types`, unique keys)
- [x] 1.3 Extend `tests/config/test_loader.py`: defaults load, custom values, missing path, missing placeholder, empty or duplicate toxicity entries, empty `types`

## 2. Types

- [x] 2.1 Add `ToxicityValue` TypedDict (`value`, `unit`, `source`) to `tools/schemas.py`

## 3. Helper

- [x] 3.1 Cache DTXSID per SMILES in `ComptoxLookup` and reuse it in `get_properties` (existing behavior and tests unchanged)
- [x] 3.2 Add `get_toxicity_values(smiles)`: fetch ToxVal records, match configured labels, skip non-numeric values, choose by source priority, report value, unit and source; same auth, failure and caching rules
- [x] 3.3 Update the `ComptoxLookup` docstring to cover both lookups

## 4. Tests

- [x] 4.1 Extend `tests/tools/informatics/helpers/test_comptox.py` with synthetic ToxVal payloads: all four values found, absent value omitted, other types ignored, alternate label (OSF), extra configured value
- [x] 4.2 Cover selection: listed source beats unlisted, earlier listed source wins, tie keeps first record, null/non-numeric skipped, unit passthrough
- [x] 4.3 Cover shared behavior: one DTXSID request for properties then toxicity, missing key raises without request, network error / 500 / malformed body return empty and are not cached, repeat lookup cached

## 5. Verification

- [ ] 5.1 Confirm labels and source names against real ToxVal output for a chemical that has RfD/RfC/SF/IUR, and adjust config if they differ
- [x] 5.2 Run `uv run ruff format .`, `ruff check .`, `pyright`, `pytest`, and the bandit command; confirm `example.json`, `example_2.json` and `tools/informatics/example.txt` are not staged
