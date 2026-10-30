## 1. Reusable kit (outside the repo, `~/Documents/claude-ui-craft/`)

- [x] 1.1 Create the kit folder with `README.md` explaining what the kit is, the four layers (design document, skill, verification command, reminder hook), integration into an existing project, integration into a new project, and how to update an installed copy
- [x] 1.2 Write `skills/ui-craft/SKILL.md` (method only, project-agnostic, defers to `frontend-design` for direction and `dataviz` for charts) and its references: `design-md-template.md` guidance, `states-checklist.md`, `verify-loop.md`
- [x] 1.3 Write `commands/ui-check.md`: locate changed surface, render light and dark (Playwright harness first, then `/run` + browser), checklist with evidence table, run `test:visual` and contrast test, never approve references unseen
- [x] 1.4 Write `hooks/ui-reminder.sh` (stdin JSON, path match, one-line reminder, exit 0, `jq` with `sed` fallback) and `hooks/settings.hooks.json` snippet
- [x] 1.5 Write templates: `DESIGN.template.md`, `frontend-CLAUDE.section.md`, `designDoc.test.ts`, `contrast.test.ts`, `vitest.visual.config.ts`, `Example.visual.tsx`
- [x] 1.6 Write `install.sh <project-root> [frontend-dir]`: copy skill and command, merge hook into `.claude/settings.json` without dropping existing hooks, scaffold `DESIGN.md` only when absent, print remaining manual steps; idempotent
- [x] 1.7 Dry-run the installer against an empty scratch project and against a scratch project with an existing `settings.json` and `DESIGN.md`; fix until both scenarios behave as the spec says

## 2. Install into this project

- [x] 2.1 Run the kit installer against this repo with `frontend` as the UI directory; confirm `.claude/skills/ui-craft/`, `.claude/commands/ui-check.md`, `.claude/hooks/ui-reminder.sh` and `.claude/settings.json` exist
- [x] 2.2 Verify the hook manually: pipe a sample `PostToolUse` payload for `frontend/src/App.tsx` (reminder shown) and for `tools/x.py` (silent)

## 3. Project design document

- [x] 3.1 Write `frontend/DESIGN.md` from `src/index.css`, `components/ui/*`, `components/layout/*` and the `web-ui-shell` spec: direction, token table (every light-theme `--token` with meaning and allowed use), type and spacing scale, materials and motion, primitive inventory with when to use, required panel states, copy rules, anti-patterns
- [x] 3.2 Add `frontend/src/designDoc.test.ts` asserting set equality between light-theme tokens in `index.css` and backticked tokens in the `DESIGN.md` tokens section; add negative cases through fixtures (undocumented token, stale token)
- [x] 3.3 Add two bullets to `frontend/CLAUDE.md`: `DESIGN.md` is the design authority (use the `ui-craft` skill for UI work); `/ui-check` must pass before UI work is done

## 4. Verification

- [x] 4.1 Run `/ui-check` once on an existing surface (the Overview ribbon) to prove the command works end to end here; record the pass/fail table in the change folder as `verification.md`
- [ ] 4.2 `npm --prefix frontend run check` passes (includes the new test); `uv run pytest tests/test_claude_md.py` passes; `uv run pre-commit run --all-files` passes
  - Status 2026-10-30: frontend check, the CLAUDE.md guard and pre-commit on this change's files pass. `--all-files` fails on pre-existing debt unrelated to this change: the trailing-comma hook reformats 213 Python files and pushes 12 functions over the 18-line limit (same finding as the previous session). Needs its own change.
- [x] 4.3 Re-run the kit installer against this repo to confirm idempotence (no diff)

## 5. Audit mode (added 2026-10-30 at the user's request)

- [x] 5.1 Add `commands/ui-audit.md` and `skills/ui-craft/references/audit-heuristics.md` to the kit; add an "Auditing an existing app" section to `SKILL.md`; update `README.md` and `install.sh`
- [x] 5.2 Reinstall the kit here; confirm `.claude/commands/ui-audit.md` exists
- [x] 5.3 Run `/ui-audit` on this app: live app in light and dark for the shell, chat, settings, monitoring and map (first-load state), approved screenshot references for the ribbon and exposure chain (ready states), static checks across `frontend/src`; write `docs/ui-audit-2026-10-30.md` with scoreboard, ranked proposals and not-assessed list
