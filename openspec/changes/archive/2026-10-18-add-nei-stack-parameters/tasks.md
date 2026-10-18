## 0. Shared Envirofacts client and EIS lookup

- [x] 0.1 `[efservice]` settings (base URL, delay, timeout, retries, backoff) with an `EfserviceSettings` loader in `config/` and negative tests; remove those keys from `[tri]`/`TriSettings` and update the TRI settings tests
- [x] 0.2 `tools/emissions/helpers/efservice.py`: `EfserviceClient.get_rows(path)` (throttle, retry/backoff, Retry-After, JSON list check, `EfserviceError`); move the tests from `test_tri.py`; `TriFetcher` uses it, behavior unchanged
- [x] 0.3 `[frs]` settings (`eis_path` with `{frs_id}`, program name, field names) with a loader and negative tests
- [x] 0.4 `tools/emissions/helpers/frs.py`: `eis_ids_for_frs(frs_id, client, settings)` returning distinct EIS IDs, with warnings instead of exceptions; tests

## 1. Data inspection (done)

- [x] 1.1 Inspect `data/raw/nei_smoke_point_2023.zip`: format, columns, ID shape, duplicates, dates, NAICS, units, candidate counts, shard sizes (findings in design.md)

## 2. Configuration

- [x] 2.1 Add `[stack.nei]` to `config/settings.toml` (directory, file template, prefix digits, id column, columns, reported units, candidate cap, merge precision, raw path, raw columns) with comments
- [x] 2.2 Add `NeiSettings` to `config/stack.py` (a field of `StackSettings`) with validation per the app-configuration delta; tests including a negative case per missing or invalid key

## 3. Compact table

- [x] 3.1 `scripts/compact_nei_stacks.py`: stream the raw zip into sorted, deterministic gzip shards per the design (D5); tests with a small synthetic zip (comment lines, repeated pollutant rows, invalid IDs, blank/zero/non-finite values, 23 vs 23.0, stale shard removal, determinism, missing column)
- [x] 3.2 Run it on the real zip; check shard count, row total (about 202,000) and that every shard is below the large-file limit; commit the shards (not the zip)

## 4. Lookup

- [x] 4.1 `tools/emissions/helpers/nei.py`: cached shard reader (by prefix), candidate building (convert/validate via `stack_values`, merge, order, cap) and warnings
- [x] 4.2 `nei_stack_candidates(frs_id, client, ...)` composing the EIS lookup and the candidates into a `NeiStackResult`; `NeiStackResult` in `tools/schemas.py`
- [x] 4.3 Tests with synthetic shards (fake IDs, round numbers) for every `stack-parameters-nei` scenario plus: integer and padded FRS ID, several EIS IDs, missing shard, missing column raises, changed file re-read, invalid rows dropped with a count, unit conversion from ft/ft/s/degF, merge, ordering and cap

## 5. Tool

- [x] 5.1 Implement `fetch_stack_parameters_from_nei(frs_id)` in `tools/emissions/stack.py` (edge builds the HTTP client); description: first choice, units, candidates must each be evaluated, fall back to the SCC tool when empty
- [x] 5.2 Update `tests/tools/emissions/test_stack.py` (replace the not-implemented test) and the registry test if needed
- [x] 5.3 Update the README (tool no longer a stub; where the shards come from and how to rebuild them; the unit assumption)

## 6. Quality gates

- [x] 6.1 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check, `pytest` and `pre-commit run --all-files` all pass
- [x] 6.2 `openspec validate add-nei-stack-parameters --strict` passes
