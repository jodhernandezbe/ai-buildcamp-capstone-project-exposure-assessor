## Why

The navigation rail offers "New analysis", "Workspace" and a list of this session's runs, but
these do not behave as a user expects: the run list is lost on reload and switching runs is
fragile, and there is no way to take the findings out of the app. An assessor needs one clear
workspace, a reliable way to wipe it and start over, and a Word report of the findings laid out
the way EPA screening assessments are written (chemical properties, data sources, releases,
exposure, risk), so the work can be reviewed and filed.

## What Changes

- **BREAKING (UI)**: the rail drops "New analysis" and the session run list. It shows, in
  order: Workspace, Clear workspace, Generate report, Monitoring, and Settings at the bottom.
  The app holds one workspace (one conversation thread) at a time.
- **Workspace** is the current view (overview, map, chat); activating it returns there from
  fullscreen or an open drawer.
- **Clear workspace** asks for confirmation in an in-app dialog, then discards the current
  thread on the server (`DELETE /api/v1/chat/threads/{id}`) and empties the chat, the overview,
  the charts and the map, with a fresh thread id. It is disabled while a turn streams or when
  the workspace is already empty. The chat header's clear button runs the same action.
- **Generate report** downloads a `.docx` built on the server from the current thread's
  workspace state and its final assistant answer. It is disabled while a turn streams or before
  any facility or chemical result exists.
- New endpoint `GET /api/v1/chat/threads/{thread_id}/report` returns the Word document. Sections
  follow an EPA screening-assessment layout: summary, chemical identity and properties, data
  sources, releases, exposure assessment, risk characterization, uncertainties and limitations,
  and the assessor (model-generated) summary, labelled as such. Values come only from the
  workspace state; absent values print as "not reported" with their reason.
- **Monitoring** appears in the rail as a disabled entry marked "Coming soon". Its content is
  out of scope here and will be defined in a later change.
- New Python dependency: `python-docx`.

## Capabilities

### New Capabilities
- `assessment-report`: the Word report endpoint, its sections, ordering, value formatting,
  provenance and the labelling of model-generated text.

### Modified Capabilities
- `web-ui-shell`: the Navigation rail requirement changes to the four actions; the Session run
  history requirement is removed; new requirements for Clear workspace (with confirmation) and
  Generate report (download, disabled states, failure message).
- `web-ui-server`: Conversation threads no longer promise that earlier threads stay in place
  when a new analysis starts (the UI now discards the thread it clears).

## Impact

- Frontend: `components/layout/LeftNavRail.tsx`, `App.tsx`, `hooks/useAgentStream.ts`,
  removal of `hooks/useRunHistory.ts` (and its tests, `App.runs.test.tsx`), a new
  confirmation dialog primitive in `components/ui/`, `services/apiClient.ts` (report download),
  chat header clear button wiring.
- Backend: `api/routers/v1_chat.py` (report route), new `api/services/report/` (document
  builder, one module per section), `api/schemas` unchanged except a documented binary response.
- Config: report title, disclaimer text, file-name pattern and section headings in
  `config/settings.toml` under `[ui.report]`.
- Dependencies: `python-docx` added to `pyproject.toml`; bandit and pip-audit must stay clean.
- Specs: `web-ui-shell`, `web-ui-server`, new `assessment-report`.
