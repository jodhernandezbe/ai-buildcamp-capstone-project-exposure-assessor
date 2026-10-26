## Context

See proposal.md for motivation. Today `App.tsx` wires `useRunHistory` (React-state run list)
and `useAgentStream.newRun` (fresh UUID, server thread left in place) to the rail's "New
analysis" and run entries; "Workspace" only closes Settings and leaves fullscreen. The chat
header's `ClearChatButton` also calls `newRun`. The server already exposes
`DELETE /api/v1/chat/threads/{id}` (reset, 409 while running) and the frontend has an unused
`resetThread()` wrapper. Each thread holds its message history and the latest `WorkspaceState`
(`api/schemas/workspace.py`), which carries every value the report needs, with sources and
warnings. `api/` must stay a thin adapter that never computes values.

## Goals / Non-Goals

**Goals:**
- One workspace per page; a confirmed, server-backed clear.
- A deterministic `.docx` built on the server from `WorkspaceState` plus the last assistant
  message, reproducible from a fixture in tests.

**Non-Goals:**
- The Monitoring view (only a disabled rail entry here).
- PDF output, charts or maps embedded in the report, report templates the user can edit.
- Persisting threads or reports on disk.

## Decisions

1. **Report built in `api/services/report/`, served by `v1_chat.py`.** The router stays thin:
   look up the thread (404/409), call `build_report(state, last_answer, settings) -> bytes`,
   return a `Response` with the Word media type and `Content-Disposition`. The builder is
   presentation of contract values, which is the `api/` layer's job; it reads no tools.
   Alternative: browser-side docx.js — rejected, it would put formatting of scientific values
   in the frontend and duplicate significant-digit rules.

2. **One module per section** (`summary.py`, `chemical.py`, `sources.py`, `releases.py`,
   `exposure.py`, `risk.py`, `uncertainties.py`, `assessor.py`) plus `document.py` (title
   block, heading/table helpers) and `values.py` (the single "value or not reported (reason)"
   formatter, significant digits from `[ui]`). Each section is a function
   `(doc, state, text) -> None`, keeping functions under 18 lines and each section testable.

3. **`python-docx`** for writing. Mature, pure Python, no network or macros. Alternative:
   hand-written OOXML — rejected as error-prone.

4. **Markdown in section 8** is converted with a small, safe subset (paragraphs, bold/italic,
   bullet and numbered lists, GFM tables, headings → bold paragraphs). Anything else is kept
   as plain text; raw HTML is printed as text. No extra Markdown dependency: a line-based
   parser covering what the agent prompt produces.

5. **Report text in config.** `[ui.report]` in `settings.toml` holds title, disclaimer,
   assessor-summary note, section headings, empty-section sentence and the file-name pattern
   (`exposure-screening-{cas}-{date}.docx`), loaded by `config.ui`. Thresholds and significant
   digits reuse the existing client settings.

6. **Clear workspace = `resetThread(current)` then local reset.** `useAgentStream` gets
   `clearWorkspace()`: call DELETE; on 204 (or 404, the thread is already gone) clear messages,
   usage, confirmation and the store, then switch to a fresh UUID; on any other error keep
   everything and surface a notice. Rejected: reusing the same thread id after reset — a fresh
   id avoids any late SSE frame of the old thread landing in the new workspace.

7. **Remove `useRunHistory`, `selectRun`, `onNewRun/onSent/onGone`.** The rail becomes four
   fixed entries. `getThread()` stays in the client for later use but loses its caller; the
   thread-snapshot endpoint is unchanged.

8. **Confirmation dialog** as a new domain-agnostic primitive `components/ui/ConfirmDialog.tsx`
   (native `<dialog>` with `showModal()`, focus return, Escape handled by the dialog layer per
   the frontend Escape rule). Never `window.confirm` (it would block browser automation too).

9. **Report download** in `services/apiClient.ts`: `fetch` → `blob` → object URL → temporary
   `<a download>` click → revoke. The file name comes from `Content-Disposition`. Busy state
   lives in a small `useReportDownload` hook.

## Risks / Trade-offs

- [Users lose a run they wanted] → explicit confirmation copy says it cannot be recovered;
  "Generate report" sits right below, so saving first is easy.
- [Assistant text in section 8 contradicts sections 1–7] → labelled as model-generated and
  explicitly not the source of values; values sections come only from the workspace.
- [Large workspaces (many facilities) → long report] → tables, one row per facility; no
  per-stack tables beyond those with evaluated scenarios. Acceptable for a screening tool.
- [New dependency surface] → `python-docx` pinned with a lower bound; pip-audit and bandit run
  in pre-commit.
- [Markdown subset misses a construct] → falls back to plain text, never drops content.

## Migration Plan

Frontend and backend ship together (single local app). No data migration: threads are in
memory. Rollback is a revert of the change.
