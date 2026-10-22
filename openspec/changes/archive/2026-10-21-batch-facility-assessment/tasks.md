## 1. Settings and shared utilities

- [x] 1.1 Add `[assessment]` (max_facilities, max_workers, scc_min_score, max_scc_stacks, inventory_cache_seconds) and `config/assessment.py` with negative tests
- [x] 1.2 Add `commons/ttl_cache.py` (thread-safe, deep copies, TTL, size cap) with tests
- [x] 1.3 Reuse the inventory through the cache (`inventory_listing`, `with_eis_ids`, `clear_inventory_cache`); `tests/conftest.py` clears it per test; test the reuse

## 2. The batch tool

- [x] 2.1 Add `tools/assessment/helpers/steps.py` (`Steps`), `stacks.py` (NEI -> PSTK by SCC -> global default, with notes), `chain.py` (per facility, thread pool in copied context), `view.py` (summary, ranking, caps)
- [x] 2.2 Add `assess_facilities` (selection, caps, benchmarks, SCC lock, both views) and register it; schemas in `tools/schemas.py`
- [x] 2.3 Tests: every stack tier and its notes, score floor, duplicates, title lookup, order and context of the pool, summary and ranking, selection by default and by ID, caps, given vs looked-up benchmarks, invalid CAS, both views
- [x] 2.4 Point the inventory and exposure descriptions to the batch tool; description tests; `tools/CLAUDE.md` exception; step label

## 3. Workspace

- [x] 3.1 Add `AssessedPayload` and `project_assessment`; exposure items attach by FRS ID when they carry one
- [x] 3.2 Tests: every facility attached, same-rate facilities kept apart, PSTK tier and SCC description, a later single result wins, invalid item and missing artifact

## 4. Verification

- [x] 4.1 `uv run pytest`, ruff, pyright, bandit, function length; all pass
- [x] 4.2 Live tool run for hexane: 25 of 25 assessed (23 NEI, 2 PSTK)
- [x] 4.3 Live agent run for hexane through the web API: 3 tool calls, 25 of 25 facilities on the map with stacks and risk, $0.07
- [x] 4.4 Re-record the eval cassettes and run `uv run pytest -m eval` 3 times: moved to the change `re-record-eval-cassette`

## 5. Tiered screening (selection bias)

- [x] 5.1 Settings: `[assessment]` max_refined, max_worst_case_listed, weather_cell_deg; `[assessment.screening]` hq, cancer_risk, ambient_temperatures_k; `[frs_eis]` twin_workers, cache_seconds; negative tests
- [x] 5.2 EIS at scale: concurrent twin searches, bulk twin registrations, reuse cache; tests
- [x] 5.3 `helpers/screening.py`: unit-rate bound, own-stack worst case over the temperatures, thresholds (no benchmark = cannot screen); tests
- [x] 5.4 Tiers in `run_assessment` and `chain.py` (stacks reused at tier 3, SCC once per title, weather once per grid cell); schemas for screened-out and worst-case-only; tests
- [x] 5.5 Model view: thresholds, tier counts, highest bound screened out, worst-case-only list (capped); artifact dict; description; tests
- [x] 5.6 Workspace: projector (dict and list artifacts), `screening` on each facility, screened-out facilities placed; frontend card wording; tests
- [x] 5.7 Prompt: cover every facility, screening not ranking; prompt test
- [x] 5.8 Gates (pytest, ruff, pyright, bandit, function length, frontend check); live hexane run (tool and agent)
- [x] 5.9 Evals judge the outcome, not the route: every facility assessed (batch or by hand) and named in the report; the chain checks apply when driven by hand. Descriptions say what each tool does, needs and returns (no cross-steering); the prompt states the coverage rule only
- [x] 5.10 The screened-out facilities closest to a threshold are listed (`max_screened_out_listed`, 5), so a report has a table even when every facility is screened out; judge and prompt output format allow it
- [x] 5.11 Live cassette re-record: moved to the change `re-record-eval-cassette` (CompTox's certificate expired 2026-10-21 23:59 GMT). Evaluated meanwhile with CompTox replayed from the committed cassette and every other tool live: 13 scored runs, 9 pass; every deterministic check passed in all 13; the 4 failures are the report judge (weather source not named)
