## 1. NAICS titles

- [x] 1.1 Download the Census six-digit 2017 and 2022 code lists to `data/raw/naics/` (ignored) and add `scripts/build_naics_titles.py` (stdlib xlsx parsing, newest vintage wins, reproducible CSV) with tests
- [x] 1.2 Add `titles_path`, `titles_code_column`, `titles_title_column` to `[industry]` and `config/industry.py`, with negative tests naming the key
- [x] 1.3 Add `tools/emissions/helpers/naics_titles.py` (`naics_titles`, `with_titles`) with tests: read-only table, normalised titles, bad rows skipped, missing file/column raises
- [x] 1.4 Add `naics_title` to `EmissionRecord`, fill it in `query_emissions_inventory`; projector shows the inventory's title with source "TRI inventory"; tests
- [x] 1.5 `fetch_facility_industry` takes the local title first and asks `REF_NAICS` only for an unlisted code; tests for both paths

## 2. Coverage

- [x] 2.1 Change the system prompt: assess every facility the inventory lists, narrow only on request, batch inputs per turn; prompt test
- [x] 2.2 Update the inventory and industry tool descriptions and `tests/tools/test_tool_descriptions.py`

## 3. EIS IDs

- [x] 3.1 Add `[frs_eis]` and `config/frs_eis.py` (bulk EIS path, site and twin paths, fields, batch size, twin distance) with negative tests
- [x] 3.2 Add `tools/emissions/helpers/inventory/eis.py` (`EisResolver`: bulk registrations, same-site twins, notes) with tests: bulk, batching, no twin, one twin, ambiguous twins, twin without registrations, name/state/coordinate checks, failure, inputs unchanged
- [x] 3.3 Add `eis_ids` and `eis_note` to `EmissionRecord`; `rank_and_cap(enrich=...)` applies the resolver to the listed facilities; inventory description documents both
- [x] 3.4 `fetch_stack_parameters_from_nei(frs_id, eis_ids=None)`: given IDs skip the FRS lookup; tests for the tool and the helper
- [x] 3.5 Live check: hexane's 25 listed facilities resolve 23 EIS IDs (one through an FRS twin 154 m away); the two others have no NEI registration under any same-named FRS record

## 4. Completion guardrail

- [x] 4.1 Add `agent/completion.py` (`CompletionGuard`, reviewer call, nudge node, routing) and wire it into `build_agent` as an opt-in exit check; nudges are named user messages
- [x] 4.2 Add `prompts/completion_check.md` and `prompts/completion_nudge.md`; `[ui.prompts]` names them and `max_nudges`; `config/ui.py` and tests
- [x] 4.3 The web program, the CLI and the evals build the agent with the check; the thread snapshot and the scope check leave nudges out
- [x] 4.4 Tests: complete reply ends, deferred reply is nudged and the agent continues with tools, the limit, a second turn, failure fails open without a traceback, routing, shipped prompts
- [x] 4.5 Prompt: never end a reply by announcing the next steps; prompt test
- [x] 4.6 Live check of a hexane run through the completion check (hexane runs through the web API on 2026-10-21; no nudge was needed)

## 5. Verification

- [x] 5.1 `uv run pytest`, `ruff format`, `ruff check`, `pyright`, `bandit`, function length; all pass
- [x] 5.2 `uv run pytest -m eval` re-run: moved to the change `re-record-eval-cassette` (CompTox's certificate expired on 2026-10-21 before the cassette could be re-recorded)
