## 1. Setup and configuration

- [x] 1.1 Add `python-docx` to `pyproject.toml` dependencies and `uv sync`; confirm `uv run pip-audit` and bandit stay clean
- [x] 1.2 Add `[ui.report]` to `config/settings.toml` (title, disclaimer, assessor-summary note, eight section headings, empty-section sentence, file-name pattern) and a typed loader in `config.ui`, with tests including a negative test for a missing heading

## 2. Report builder (`api/services/report/`)

- [x] 2.1 Create `values.py`: one formatter for "value + unit, configured significant digits" or "not reported (reason)"; tests for absent, `None` reason, non-finite and normal values
- [x] 2.2 Create `document.py`: title block, numbered heading, table and empty-section helpers over `python-docx`
- [x] 2.3 Create `summary.py` (section 1) and `chemical.py` (section 2) with tests against workspace fixtures
- [x] 2.4 Create `sources.py` (section 3): collect distinct sources from chemical, stacks (with tier), industry, operating hours, receptors, meteorology; tests for de-duplication
- [x] 2.5 Create `releases.py` (section 4) and `exposure.py` (section 5); tests including a facility with no stacks evaluated
- [x] 2.6 Create `risk.py` (section 6) with thresholds from client settings, and `uncertainties.py` (section 7) listing warnings, screening defaults and unattributed results
- [x] 2.7 Create `assessor.py` (section 8): safe Markdown subset (paragraphs, emphasis, lists, GFM tables) to document elements, raw HTML printed as text, model-generated label note; tests for a table and for `<script>`
- [x] 2.8 Create `build_report(state, last_answer, settings) -> bytes` assembling all sections in order; test that headings appear in configured order and that every number in sections 1–7 appears in the source fixture
- [x] 2.9 Add a helper returning the thread's last assistant message text (reuse `snapshots.thread_messages`)

## 3. Report endpoint

- [x] 3.1 Add `GET /api/v1/chat/threads/{thread_id}/report` to `api/routers/v1_chat.py`: 404 unknown, 409 running or nothing to report, 422 malformed id, Word media type and `Content-Disposition` file name
- [x] 3.2 Tests in `tests/api/` for each status code, the attachment name, that no tool or model is called, and that the document holds no key material (fake vault with a sentinel key)
- [x] 3.3 Document the binary response in the OpenAPI route; run `uv run python -m scripts.export_contract` and `npm --prefix frontend run gen:types` (expect no schema change)

## 4. Frontend: clear workspace

- [x] 4.1 Add `components/ui/ConfirmDialog.tsx` (native dialog, Escape handled by the top layer, focus returns to opener) with tests
- [x] 4.2 Add `clearWorkspace()` to `hooks/useAgentStream.ts`: `resetThread`, then reset messages, usage, confirmation and the workspace store and switch to a fresh thread id; on failure keep state and set a notice. Tests for success, 404 and 500
- [x] 4.3 Remove `newRun`, `selectRun` and the run callbacks from `useAgentStream`; delete `hooks/useRunHistory.ts`, its test and `App.runs.test.tsx`
- [x] 4.4 Route the chat header's clear button through the same confirmed `clearWorkspace` action

## 5. Frontend: report and rail

- [x] 5.1 Add `downloadReport(threadId)` to `services/apiClient.ts` (blob, file name from `Content-Disposition`, object URL revoked) and a `useReportDownload` hook with busy state; tests with a fake fetch
- [x] 5.2 Rewrite `LeftNavRail.tsx`: Workspace (current page), Clear workspace, Generate report, Monitoring (disabled, "Coming soon"), Settings at the bottom; disabled tooltips explain why; remove the run list and "New analysis"
- [x] 5.3 Wire the rail in `App.tsx`: Workspace closes Settings/dialogs and leaves fullscreen; Clear opens the dialog; Report enabled only when idle and the workspace has a chemical or facility; error notices shown
- [x] 5.4 Update `LeftNavRail.test.tsx` and `App.test.tsx` for the spec scenarios (order, disabled states, cancel, clear success/failure, download, monitoring inert)

## 6. Docs and verification

- [x] 6.1 Update `frontend/CLAUDE.md` (run list wording) and `api/CLAUDE.md` (report service) where they describe the rail or the thread routes
- [x] 6.2 Run the full gate: `uv run pytest`, ruff format/check, pyright, bandit, function-length check, `npm --prefix frontend run check`, `uv run pre-commit run --all-files`
- [x] 6.4 Report review follow-up: risk by TSCA life cycle stage and condition of use first in section 6, stages and conditions of use named in section 1, app logo and name in the page header, "Page X of Y" footer (`[ui.report]` `brand`, `logo`, `page_label`)
- [x] 6.3 Manually generate a report from a real assessment run, open it in Word, and check sections against the overview panel
