## 1. Configuration

- [x] 1.1 Add the `[qpc]` section to `config/settings.toml` (url_template, allowed_host, lag_quarters, sheet_name, code_header, hours_header, title_pattern, naics_edition, naics_edition_pattern, min_hours, max_hours_per_week, min_codes, timeout_seconds, max_bytes, output_path), with comments saying what each is for
- [x] 1.2 Add `config/qpc.py` (`QpcSettings` frozen dataclass, `get_qpc_settings()` cached, validators from `config/parsing.py`; https + host check, `{year}`/`{quarter}` placeholders, regex compiles, finite positive bounds)
- [x] 1.3 Add `tests/config/test_qpc.py`: defaults load; each invalid value (negative lag, non-https/foreign host, missing placeholder, bad regex, bool/NaN/zero bounds) fails naming its key

## 2. Release selection and download

- [x] 2.1 Add `scripts/qpc/__init__.py` and `scripts/qpc/release.py` (`Release`, `release_for`, `release_url`); tests for 2026 Q4 -> Q2, 2026 Q2 -> 2025 Q4, 2026 Q1 -> 2025 Q3, lag 0, year rollover
- [x] 2.2 Add `scripts/qpc/errors.py` (`QpcError`, `QpcLayoutError`, `QpcDownloadError`, `QpcDataError`)
- [x] 2.3 Add `scripts/qpc/download.py` (`fetch_workbook` with injected `httpx.Client`, timeout, streamed size cap, 404 message naming release and URL, ZIP magic check); `MockTransport` tests for 200, 404, HTML-with-200, oversized, timeout

## 3. Reading the workbook

- [x] 3.1 Add `scripts/qpc/workbook.py`: sheet-by-name lookup through `workbook.xml` and its rels, typed cell values (shared/inline strings, numbers, blanks; unknown cell types raise), cap on uncompressed member size; a test helper that builds a small xlsx in memory
- [x] 3.2 Tests: sheet found by name when it is not first, missing sheet error lists the sheets present, whitespace in headers, ints vs strings in the code column
- [x] 3.3 Add `scripts/qpc/table.py` layout discovery: title year/quarter check, header row by label, quarter block by the `Quarter N` row, hours column inside the block, NAICS edition check against the Introduction tab; tests for wrong quarter, wrong year, missing column, previous-quarter block not read, edition mismatch

## 4. Codes and values

- [x] 4.1 Add `scripts/qpc/codes.py` `parse_codes` (footnote marker, int cells, comma lists, ranges in first and later tokens); tests for `3111,7,8`, `3321,2,4-6`, `332992-4`, `334412,6-9`, `51312 3/`, `31-33 1/`, int `3112`, and garbage rejected
- [x] 4.2 Add `to_four_digit` (4-digit as is, 3-digit through the titles table for the configured edition, 5/6-digit and shorter skipped with reasons); tests including a 3-digit row with children from a fake titles table and a 3-digit row with none
- [x] 4.3 Add row classification in `table.py`: hours validation (finite, not bool, 0 < h <= 168, `D` withheld, other strings rejected), overlap removal, code-looking cell with no parse reported; tests for 168 kept, 0 / -1 / 169 / NaN / True rejected, `D`, overlap, and the 32411 + 32412,9 case leaving 3241 absent
- [x] 4.4 Add the structural checks (no data rows, fewer than `min_codes`, empty description) as `QpcDataError`/`QpcLayoutError`; tests for each

## 5. Output and script

- [x] 5.1 Add `scripts/qpc/output.py`: Arrow table with the specified schema, sorted by code, schema metadata (release, URL, SHA-256, retrieved date, NAICS edition, sheet), atomic write (temp file + `os.replace`); tests for schema, uniqueness, metadata, determinism of rows on re-run, and that a failure or interrupted write leaves the previous file byte-identical with no temp file left
- [x] 5.2 Add `scripts/build_census_qpc_baseline.py` `main(argv, *, today, client)` wiring release -> download -> read -> classify -> write, a printed summary with the skipped-rows table, return codes 0/1 with errors on stderr; end-to-end test with an in-memory workbook and a fixed date 2026-10-22 (-> 2026 Q2)
- [x] 5.3 Confirm every spec scenario in `specs/census-qpc-baseline/spec.md` has a test (including all negatives)

## 6. First real run and gates

- [x] 6.1 Run `uv run python -m scripts.build_census_qpc_baseline` once against the real 2026 Q2 file, review the skipped-rows report against the workbook (3 `D` rows, 5/6-digit rows, `31-33`), set `min_codes` from the result, and commit `data/census_qpc_baseline.parquet`
- [x] 6.2 Spot-check a handful of parquet rows against the workbook by hand (a group row, a 3-digit row, a 168-hour row); note the check in the commit message
- [x] 6.3 Run `uv run pytest`, `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, bandit, the function-length check (<= 18) and `uv run pre-commit run --all-files`; add the script to the README/docs list of data build scripts if one exists
