## Why

The frontend already has design tokens, HIG primitives, a Playwright visual harness and a
contrast test, but the knowledge of *how the UI should look and behave* lives only in scattered
`frontend/CLAUDE.md` bullets and in the heads of whoever last prompted for it. Every new panel is
re-described in chat, so visual quality depends on the prompt rather than on the project. Experts
who get consistent UI from Claude Code without repetitive prompting move that knowledge into
files the agent loads automatically: a design document, a skill carrying the design method, a
self-run visual verification step, and a hook that triggers it. This change adds that layer here
and packages it so the same method can be dropped into other projects in minutes.

## What Changes

- Add `frontend/DESIGN.md`: the agent-facing design system for this app (direction, token
  meanings, type and spacing scale, materials and motion, component inventory with "when to
  use", the states every panel must have, copy rules, anti-patterns). Derived from the code that
  exists today; it does not restyle anything.
- Point `frontend/CLAUDE.md` at `DESIGN.md` and require the visual verification step before UI
  work is called done.
- Add a project-level `ui-craft` skill (`.claude/skills/ui-craft/`) that encodes the method:
  read `DESIGN.md` (or bootstrap it when absent), commit to a direction before coding, compose
  from existing primitives and tokens, cover every required state, then verify visually.
- Add a `/ui-check` slash command (`.claude/commands/ui-check.md`) that runs the UI, screenshots
  the changed surface in light and dark, checks it against `DESIGN.md`, and runs the visual and
  contrast tests.
- Add a project `.claude/settings.json` with a `PostToolUse` hook that, after any edit to a
  frontend source file, reminds the agent to run `/ui-check` before finishing. No heavy work runs
  in the hook.
- Add a frontend test that keeps `DESIGN.md` truthful: every design token declared in
  `src/index.css` must be documented, and every documented token must exist.
- Create a reusable kit outside this repository at `~/Documents/claude-ui-craft/` holding the
  skill, the command, the hook, a `DESIGN.md` template, the visual-test and contrast-test
  templates, an `install.sh` that copies them into a target project, and a `README.md` that
  explains integration step by step. This project is the first installation of that kit.
- Figma, Storybook and any external design tool are out of scope: everything runs inside
  Claude Code.

## Capabilities

### New Capabilities
- `ui-design-workflow`: the agent-facing design layer of the frontend: a design document the
  agent must follow, a verification command, a reminder hook, and a consistency test tying the
  document to the design tokens.

### Modified Capabilities
- (none: the visual language itself, specified in `web-ui-shell`, does not change)

## Impact

- New files: `frontend/DESIGN.md`, `frontend/src/designDoc.test.ts`, `.claude/skills/ui-craft/**`,
  `.claude/commands/ui-check.md`, `.claude/hooks/ui-reminder.sh`, `.claude/settings.json`.
- Edited: `frontend/CLAUDE.md` (two bullets), `frontend/src/index.css` only if a token needs a
  comment; no component or style changes.
- Outside the repo: `~/Documents/claude-ui-craft/` (new folder, not tracked by this repo).
- No Python, API or agent changes; no new runtime dependencies. The frontend `check` script
  picks up the new Vitest test automatically.
