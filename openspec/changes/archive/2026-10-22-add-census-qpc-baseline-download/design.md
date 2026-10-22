## Context

The QPC workbook (e.g. `2026-qtr-table-final-q2.xlsx`, ~65 kB, posted 2026-09-14) has six tabs:
Introduction, `FULL Utilization Rates`, `EMERGENCY Utilization Rates`, Table 3a, Table 3b,
Appendix. I inspected the Q2-2026 file; what the script must cope with:

- `FULL Utilization Rates`: title in A1 (`... Full Rates: 2026 Quarter 2`), year in row 3 and
  `Quarter 2` / `Quarter 1` in row 4 over two side-by-side blocks, header in row 5 (columns:
  code, description, flag, utilization rate, SE, **Average plant hours per week in operation**,
  SE, ... then the same for the previous quarter). Header cells have trailing spaces. Data rows 7-100,
  footnotes from row 102.
- The code column is not 4-digit: 94 rows of 2-, 3-, 4-, 5-, 6-digit codes, a mix of ints and
  strings (`3112` vs `'3121'`), groups (`'3111,7,8'`, `'3321,2,4-6'`, `'334412,6-9'`,
  `'332992-4'`), footnote markers (`'31-33 1/'`, `'51312 3/'`) and the aggregate `31-33`.
- Hours cells are numbers, except `D` (withheld; 3 rows). The standard error can be `Z` (< 0.05)
  and hours of exactly `168` (continuous operation, 24 x 7) are legitimate, e.g. refineries.
  No value exceeded 168 in this file.
- Earlier releases exist at the same URL pattern (`2025-qtr-table-final-q4.xlsx`, 200 OK); Q3 2026
  is 404, which is why the lag exists.
- The Introduction states the NAICS edition ("2022 edition"); the project's
  `data/naics_titles.csv` has a `vintage` column (2017, 2022).

Existing precedent: `scripts/build_naics_titles.py` reads xlsx with the standard library
(zip + XML) and the repo has no openpyxl/pandas dependency. `pyarrow` and `httpx` are declared.

## Goals / Non-Goals

**Goals:** a re-runnable script producing one trustworthy, committed parquet keyed by 4-digit NAICS
code; fail closed on anything unexpected; every changeable detail in `config/`.

**Non-Goals:** using the baseline in a tool or the agent; the EMERGENCY tab; utilization rates;
finer-than-4-digit data; scheduling the download.

## Decisions

1. **Where it lives.** `scripts/build_census_qpc_baseline.py` with `main(argv)`, like the other
   build scripts; `scripts/` is a developer package (no application imports it). Small helpers are
   separate modules so each stays one responsibility and every function is <= 18 lines:
   - `scripts/qpc/release.py`: `release_for(today, lag_quarters) -> Release` (frozen dataclass of
     year and quarter) and `release_url(template, release)`. Pure; quarter arithmetic as
     `index = year * 4 + (quarter - 1) - lag`.
   - `scripts/qpc/download.py`: `fetch_workbook(url, *, timeout, max_bytes, client) -> bytes`
     streaming with a cap, then check the `PK` ZIP magic. `httpx.Client` is injected; the default
     is built only in `main`.
   - `scripts/qpc/workbook.py`: stdlib xlsx reader that resolves a sheet by **name** via
     `xl/workbook.xml` + `xl/_rels/workbook.xml.rels` (the existing reader only takes `sheet1`),
     returns rows as lists of typed cells (shared string -> `str`, numeric -> `int | float`,
     blank -> `None`). Inline strings and the `t="str"` / `t="b"` / `t="e"` cell types are handled
     explicitly; an unknown type is an error, not a guess.
   - `scripts/qpc/codes.py`: `parse_codes(cell) -> tuple[str, ...]` and `to_four_digit(...)`.
   - `scripts/qpc/table.py`: locate header / block / column, read rows, classify each into
     "kept" or "skipped(reason)".
   - `scripts/qpc/output.py`: build the Arrow table and write it atomically.
   The `scripts/qpc/` subpackage keeps these together without crowding `scripts/`. The existing
   `build_naics_titles.py` is not edited (open/closed); a shared reader can be extracted later on
   the third use.

2. **Release choice (pure and injectable).** `main(argv, *, today=date.today, client=None)`.
   `lag_quarters = 2` is a config value. Examples in the spec cover Q1/Q2/Q4 and the year rollover.
   A 404 is a hard error naming release and URL; there is no "try the previous quarter" fallback
   because silently using another vintage hides exactly the thing the lag is meant to control.

3. **Config.** `[qpc]` in `settings.toml`, loaded by `config/qpc.py` (`QpcSettings`, frozen,
   `get_qpc_settings()` with `lru_cache`, validators from `config/parsing.py`), one module per
   concern as the project does. Keys: `url_template` (https, host `www2.census.gov`, `{year}` and
   `{quarter}`), `allowed_host`, `lag_quarters` (int >= 0), `sheet_name`
   (`FULL Utilization Rates`), `code_header` (`NAICS Code(s)`), `hours_header`
   (`Average plant hours per week in operation`), `title_pattern` (regex with year and quarter
   groups for A1), `naics_edition` (2022) and `naics_edition_pattern` (searches the Introduction
   tab), `min_hours` (exclusive, 0) and `max_hours_per_week` (168), `min_codes`, `timeout_seconds`,
   `max_bytes`, `output_path`. `output_path` resolves against the project root, like
   `titles_path`. The 168 bound is a physical fact (hours in a week) and is still a config value
   so the number lives in one place.

4. **Find things by label.** The header row is the first row (within a configured number of rows
   from the top) whose first cell, whitespace-normalised and case-folded, equals `code_header`.
   Quarter blocks are found from the row above it that holds `Quarter N`: the block whose label
   matches the requested quarter *and* the title's year is used; the hours column is the first
   cell equal to `hours_header` at or after that block's first column and before the next block.
   Today that is column F (6th), but the script never assumes it. If the requested quarter does
   not appear exactly once, or the title says another year/quarter, it raises `QpcLayoutError`.

5. **Turning published codes into 4-digit codes (decision made with the user: whole-code coverage
   only).** `parse_codes` removes a trailing footnote marker (`\s+\d+/$`) and spaces, treats ints
   via `str`, then splits on commas. The first token is the base (`3111`), each later token
   replaces the **last len(token)** digits of the base (`7` -> 3117; `4-6` -> 3324..3326). A range
   token is `<a>-<b>` where `<b>` is the final digit: in the first token `332992-4` means 332992
   to 332994, in a later token `4-6` means the base with its last digit 4 to 6. Anything not `\d+(-\d+)?` per token raises `ValueError` and the row is skipped
   with that reason. Then `to_four_digit` by code length:
   - 4 digits: the code itself;
   - 3 digits: the distinct 4-digit prefixes of that code in `data/naics_titles.csv` whose
     `vintage` equals the configured edition (children come from data, not a hard-coded list;
     none found -> skipped);
   - 5 or 6 digits: **skipped, `covers only part of a 4-digit code`** (a 4-digit code is not
     the sum of one of its children, and the file gives no weights to combine them);
   - 2 digits or fewer (`31-33`): skipped, `aggregate`.
   Mixed-length groups inside a single cell are rejected as unparseable rather than interpreted.
   The consequence the user accepted: 3241 (refineries 32411 + asphalt 32412,9), 3251, 3262,
   3273, 3119 and others split across 5/6-digit rows have no 4-digit value; the run report lists them.
   A later change can add a rollup rule or finer granularity without touching the rest.

6. **Value validation (fail closed).** Hours must be an `int | float` that is not a `bool`,
   finite, `> min_hours` and `<= max_hours_per_week`. `D` becomes `skipped: withheld`. Any other
   string, blank hours with a populated code, or out-of-range value becomes `skipped: <reason>`.
   After expansion, a 4-digit code claimed by two rows is removed and both rows are reported
   (`overlaps another row`). The 168 bound is *inclusive*.
   Only the structure checks abort the run: header/column/sheet/quarter/edition mismatches,
   fewer than `min_codes` surviving codes (the value is set during implementation from the
   first real run, conservatively below it), or no data rows. Individual bad rows never abort; they
   are excluded and reported.

7. **Output schema and versioning.** Columns: `naics_code` (utf8), `avg_plant_hours_per_week`
   (float64), `source_naics`, `source_title`, `release_year` (int16), `release_quarter` (int8).
   Sorted by `naics_code`. Schema metadata (Arrow `replace_schema_metadata`, bytes keys):
   `qpc.release` (`2026Q2`), `qpc.url`, `qpc.sha256` (of the downloaded bytes), `qpc.retrieved`
   (UTC date), `qpc.naics_edition`, `qpc.sheet`. Written with `pyarrow.parquet.write_table` to a
   temp file in the same directory, then `os.replace`, so a crash or failed check never leaves a
   partial or half-new file. Compression and `use_dictionary` are fixed so identical input gives
   identical row data; only `qpc.retrieved` differs between runs, and that is intended
   ("versioned in the data" = committed in git, with the release inside the file and in each row).
   `data/` is already committed (e.g. `naics_titles.csv`), so the parquet is added the same way.

8. **Report.** `main` prints a one-line header (release, URL, sha256 prefix), the number of codes
   written, and a table of skipped rows (`source code | title | reason`). It returns 0 on success
   and 1 with a stderr message on any `QpcError` (a single exception base with `QpcLayoutError`,
   `QpcDownloadError`, `QpcDataError`). Exceptions caught are only these and `httpx.HTTPError`,
   `zipfile.BadZipFile`, `ElementTree.ParseError`; nothing is swallowed.

9. **XML safety.** The workbook is untrusted. Parsing uses `xml.etree.ElementTree` as the existing
   script does (`# noqa: S314` with a reason), mitigated by the size cap on the download, a cap on
   total uncompressed size of the members read (guarding zip bombs), and reading only the three
   members needed. `defusedxml` is not added; if the maintainers prefer it, swapping the parse call
   is one line.

10. **Tests (mirror the layout, no network).** `tests/config/test_qpc.py`,
    `tests/scripts/qpc/test_release.py`, `test_codes.py`, `test_table.py`, `test_workbook.py`,
    `test_output.py`, `test_download.py`, and `tests/scripts/test_build_census_qpc_baseline.py` for
    `main`. A test helper builds a tiny xlsx in memory (zip of the three XML parts) with synthetic
    labels and obviously fake values (e.g. 11.0, 22.0, 168), as the project forbids invented values
    that look like real data. Download tests use `httpx.MockTransport`. Every spec scenario has a
    test, including the negatives (wrong quarter, wrong edition, missing column, `D`, 0/-1/169/NaN/
    `True`, overlap, 404, HTML-with-200, oversized, too few codes, interrupted write leaves the old
    file). One opt-in check, outside the default run, can validate a locally downloaded real
    workbook against the committed parquet.

## Risks / Trade-offs

- **Coverage loss from the whole-code rule.** Every 5/6-digit row (in the Q2-2026 file these
  include refineries and petrochemicals, the most chemically interesting ones) produces no
  4-digit value.
  Accepted deliberately to avoid invented numbers; the run report makes the gap visible and the
  parquet's `source_naics` makes the origin of every kept value auditable.
- **Upstream layout drift.** Label-based discovery plus hard failure on mismatch turns drift into a
  visible error instead of a bad file; the cost is that a rename needs a config edit.
- **File naming drift.** The URL pattern held for the releases checked (2024 Q4 - 2026 Q2); if
  Census changes it, the 404 error names the URL and the template is a config value.
- **Group semantics.** `3111,7,8` assigns one value to three industries; it is the published
  granularity, recorded in `source_naics` so consumers can tell a group value from a single-code one.
- **Retrieval date in metadata** makes the file differ between identical runs; rows do not.
- **Revisions.** Census notes that data may be revised in later releases; re-running at a later
  date can change values with the same release label (the SHA-256 in the metadata shows it).

## Open Questions

None blocking. Assumed and recorded: the previous-quarter block is ignored; the `c` coverage flag
on utilization rates does not apply to hours and is ignored; hours of exactly 168 are valid.
