## 1. Configuration and types

- [x] 1.1 `[industry]` in `config/settings.toml` and `config/industry.py` with validation and tests (a negative case per key)
- [x] 1.2 `[tri] recent_years`, `{after_year}` in the release path, `doc_ctrl_num` field; `after_year` / `first_year` methods; tests
- [x] 1.3 `FacilityIndustry`, `EmissionRecord.doc_ctrl_num` and `ExposureMetrics.stack_source` in `tools/schemas.py`

## 2. Inventory window and control number

- [x] 2.1 TRI request filters recent years; reducer keeps the control number, counts rows outside the window; tests

## 3. Lookup, tool and SCC guard

- [x] 3.1 `tools/emissions/helpers/industry/naics.py`: control number -> primary row -> origin -> title; warnings instead of exceptions; tests for every scenario
- [x] 3.2 `tools/emissions/industry.py`: the `@tool` with the full description; register it; tool tests
- [x] 3.3 SCC lookup: drop numeric codes, refuse a code-only description; tests
- [x] 3.4 Descriptions point to the EPA global default stack when industry or SCC is unknown; description-audit tests; live smoke test (no key)

## 4. Generic stack warning

- [x] 4.1 `calculate_exposure_metrics` echoes `stack_source` and warns for global default and PSTK stacks; tests

## 5. Coordinates from FRS

- [x] 5.1 `[frs_point]` settings, `FrsLocator`, reducer fallback, inventory wiring; unit tests and a live smoke test

## 6. Gates

- [x] 6.1 README updated
- [x] 6.2 ruff, pyright, bandit, function length, pytest, pre-commit all pass
- [x] 6.3 `openspec validate add-facility-industry-tool --strict` passes
