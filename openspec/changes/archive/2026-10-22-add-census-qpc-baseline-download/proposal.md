## Why

Screening-level exposure needs to know how many hours a week a plant in a given industry runs, and
the Census Bureau's Quarterly Survey of Plant Capacity Utilization (QPC) publishes that as
"Average plant hours per week in operation". The data exists only as a quarterly Excel workbook
whose layout is not analysis-ready: the "FULL Utilization Rates" tab mixes 3-, 4-, 5- and 6-digit
NAICS codes, comma/range groups (`3111,7,8`, `3321,2,4-6`, `334412,6-9`), footnote markers
(`31-33 1/`), withheld cells (`D`) and two quarters side by side. We need a reproducible,
validated, committed baseline keyed by 4-digit NAICS code before any tool can use it.

## What Changes

- Add a developer script, `scripts/build_census_qpc_baseline.py`, that downloads the QPC workbook
  for the release **two quarters behind the current one** (2026 Q4 -> 2026 Q2; 2026 Q2 -> 2025 Q4;
  the Q2-2026 table was posted 2026-09-14, so the lag is what makes the file exist) and writes
  `data/census_qpc_baseline.parquet`.
- Read only the `FULL Utilization Rates` tab and only the "Average plant hours per week in
  operation" column of the requested quarter's block (the sheet also carries the previous quarter).
- Locate the header, quarter block and column by their text, not by position, and refuse to write
  when the workbook is not what was asked for (wrong quarter or NAICS edition, header or column
  missing, too few usable rows, non-numeric or implausible hours).
- Expand each published code expression into 4-digit NAICS codes. A 4-digit code gets a value only
  when one source row covers it entirely (4-digit rows, groups of 4-digit codes, and 3-digit rows
  expanded to their 4-digit children). Rows that cover only part of a 4-digit code (5/6-digit
  rows such as 32411 Petroleum refineries), aggregates (`31-33`), and withheld cells (`D`) are not
  guessed or averaged: they are left out and listed with a reason.
- Version the output: the parquet is committed under `data/`, and carries the release it came from
  (year, quarter, URL, workbook SHA-256, retrieval date) in its file metadata and per-row source
  columns, so a diff shows exactly which release changed it.
- Put everything that can change in `config/settings.toml` with a typed loader `config/qpc.py`:
  URL template, quarters of lag, sheet name, header labels, plausibility bounds, NAICS edition,
  output path, timeout and size cap.

## Capabilities

### New Capabilities
- `census-qpc-baseline`: selecting the QPC release by lag, downloading and validating the workbook,
  expanding published NAICS code expressions to 4-digit codes, and writing the versioned parquet of
  average plant hours per week.

### Modified Capabilities
<!-- None: no existing requirement changes. Consuming the baseline in a tool is out of scope. -->

## Impact

- New: `scripts/build_census_qpc_baseline.py` (plus small helper modules in `scripts/`),
  `config/qpc.py`, a `[qpc]` section in `config/settings.toml`, `data/census_qpc_baseline.parquet`,
  tests under `tests/scripts/` and `tests/config/`.
- Dependencies: none added. The workbook is read with the standard library (as
  `scripts/build_naics_titles.py` already does) and written with `pyarrow` and `httpx`, both
  already declared.
- Network: the script calls `www2.census.gov` when run by a developer; no runtime or test path
  touches the network (tests inject the fetch).
- Out of scope: using the baseline in the agent or any tool; the EMERGENCY tab; utilization rates
  and standard errors; 5/6-digit granularity.
