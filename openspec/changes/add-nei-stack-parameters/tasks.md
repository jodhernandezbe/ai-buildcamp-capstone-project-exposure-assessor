## 1. Inspect the data (no production code)

- [ ] 1.1 Receive the NEI file from the user; record its delimiter, header, row count, size, and the columns for FRS ID (or the facility ID it uses), stack height, diameter, exit velocity, exit temperature and their units
- [ ] 1.2 Check how many facilities have several release points, how many rows have zeros or blanks, and whether FRS IDs are digit strings; if the file is not keyed by FRS ID, decide the crosswalk with the user and update D2
- [ ] 1.3 Convert the file to `data/nei_stacks.csv` (UTF-8, comma-separated, one header row), strictly: nothing is written if a row is malformed; keep the original untouched

## 2. Configuration

- [ ] 2.1 Add `[stack.nei]` to `config/settings.toml` (path, FRS ID column, value columns, reported units) with comments
- [ ] 2.2 Add `NeiSettings` to `config/stack.py` with validation per the app-configuration delta; tests including a negative case per missing or invalid key

## 3. Lookup

- [ ] 3.1 `tools/emissions/helpers/nei.py`: cached reader keyed by FRS ID (exact digit-string match, integer accepted), release-point selection (tallest valid, file-order tie-break) and warnings, reusing `stack_values`
- [ ] 3.2 Tests with synthetic fixture CSVs (fake FRS IDs, round numbers) for every `stack-parameters-nei` scenario plus: integer and padded FRS ID, extra leading zero does not match, missing file, missing column raises, changed file re-read, non-finite/boolean/non-positive/out-of-range values, unit conversion from ft/ft/s/degF

## 4. Tool

- [ ] 4.1 Implement `fetch_stack_parameters_from_nei(frs_id)` in `tools/emissions/stack.py` using the helper and the configured settings; accept text or integer FRS IDs; keep the description accurate (first choice, units, fall back to the SCC tool)
- [ ] 4.2 Update `tests/tools/emissions/test_stack.py` (replace the not-implemented test) and the registry test if needed
- [ ] 4.3 Update the README line that lists this tool as a stub and say where the NEI CSV goes

## 5. Quality gates

- [ ] 5.1 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check, `pytest` and `pre-commit run --all-files` all pass
- [ ] 5.2 `openspec validate add-nei-stack-parameters --strict` passes
