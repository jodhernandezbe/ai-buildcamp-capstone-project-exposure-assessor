## Context

See proposal.md for motivation. Current state that shapes the approach:

- Tokens already live as CSS variables in `frontend/src/index.css` (light `:root`, dark media
  block, Tailwind `@theme inline` aliases). `contrast.test.ts` parses the same file with a regex.
- `components/ui/` holds domain-agnostic primitives (GlassCard, StatusPill, TierPill,
  SegmentedBar, Banner, Accordion, BottomDrawer, ConfirmDialog, InfoTooltip, ScenarioView,
  BrandLogo); `components/layout/` holds the shell (SplitWorkspace, PanelFrame, PanelHeader,
  rails). Features compose them.
- `vitest.visual.config.ts` renders `*.visual.tsx` in Playwright Chromium in light and dark and
  compares with `__screenshots__/`. Only the exposure chain has a visual test today.
- Anthropic's `frontend-design` skill is installed at user scope. It defers to a documented
  design system; it is a direction-setting skill, not a project-workflow skill.
- `/run` and Claude in Chrome are available in this environment for driving the live UI.
- Root `CLAUDE.md` sits exactly at the 80-line limit, so no root edit; `frontend/CLAUDE.md`
  carries the pointers.
- The project has no `.claude/settings.json` yet; `.claude/` holds OpenSpec skills and commands.

## Goals / Non-Goals

**Goals:**
- Make the design knowledge load automatically (document + skill + hook), so new UI needs no
  descriptive prompting.
- Make verification a routine the agent runs itself, with evidence.
- Keep the kit generic so another project gets the same workflow with one command.
- Keep the document honest with a test, not with discipline.

**Non-Goals:**
- No visual restyle, no new components, no token renames.
- No Figma, Storybook or external design tool.
- No CI visual gate changes (the existing `test:visual` stays developer-run).
- No hook that runs tests or browsers; hooks only remind.

## Decisions

1. **One `frontend/DESIGN.md` next to `frontend/CLAUDE.md`, not a section inside it.**
   `CLAUDE.md` is rules (short, always loaded); `DESIGN.md` is reference (longer, loaded by the
   skill and the command when UI work starts). Alternative: fold into `CLAUDE.md`, rejected
   because it would double the always-loaded context for every frontend task, including
   non-visual ones.

2. **Token table in `DESIGN.md` is machine-checked by a Vitest test (`src/designDoc.test.ts`).**
   It extracts `--name` declarations from the light `:root` block of `index.css` (same approach
   as `contrast.test.ts`) and the backticked `--name` entries from the "Tokens" section of
   `DESIGN.md`, then asserts set equality. Alternative: generate the table from CSS; rejected
   because the human-written *meaning* column is the value, and a generator would not check it.

3. **Skill name `ui-craft`, installed in the project at `.claude/skills/ui-craft/`, with the kit
   as upstream.** A copy checked into the repo means anyone cloning the project gets the workflow
   without installing anything. The kit's `install.sh` re-copies on update. Alternative: a
   user-scope or plugin install only; rejected because the workflow would then be invisible to
   collaborators and CI-less clones. The duplication is one folder and the README names the kit
   as the source of truth.

4. **Skill content is method, not taste.** The skill says: read `DESIGN.md`; if absent, derive it
   (from stylesheet and components, or from a brief) and confirm the direction; compose from
   primitives and tokens; cover the required states; finish with `/ui-check`. Taste lives in
   `DESIGN.md` per project. For new direction choices the skill defers to the installed
   `frontend-design` skill, so nothing it says is duplicated. For charts it defers to `dataviz`.

5. **`/ui-check` is a command (Markdown prompt) rather than a script.** The check is partly
   judgement (does the screenshot honour the direction, is colour the only cue), partly mechanical
   (`npm --prefix frontend run test:visual`, the contrast test). A command lets the agent use
   whichever browser tool is available (`/run`, Claude in Chrome, or the Playwright harness) and
   write the pass/fail table with evidence. Mechanical parts stay in the existing npm scripts.

6. **Reminder hook is a `PostToolUse` hook on `Edit|Write|MultiEdit` running a tiny shell
   script.** The script reads the tool input JSON from stdin, extracts `file_path`, and prints the
   reminder only when the path matches `frontend/src/**/*.{tsx,css}`. It uses `jq` when present
   and a `sed` fallback otherwise, exits 0 always, and never blocks. Alternative: a `Stop` hook
   that inspects `git diff`; rejected because it fires on every stop, including non-UI sessions,
   and needs git state.

7. **Kit location `~/Documents/claude-ui-craft/`, flat and copy-based.** Layout:
   `README.md`, `install.sh`, `skills/ui-craft/{SKILL.md,references/*.md}`,
   `commands/ui-check.md`, `hooks/{ui-reminder.sh,settings.hooks.json}`,
   `templates/{DESIGN.template.md,frontend-CLAUDE.section.md,designDoc.test.ts,contrast.test.ts,vitest.visual.config.ts,Example.visual.tsx}`.
   `install.sh <project-root> [frontend-dir]` copies the skill and command, merges the hook into
   `.claude/settings.json` (creating it, or appending to the `PostToolUse` array with `jq`;
   without `jq` it prints the snippet to paste), scaffolds `DESIGN.md` if missing, and prints
   the manual steps (add the test files, add the npm scripts). Templates are copied, never
   symlinked, so installed projects do not depend on the kit's path.

8. **The frontend path is a parameter.** This project's UI is in `frontend/`; others may use
   `web/`, `client/` or the repo root. The installer takes it as the second argument and the hook
   script reads a `UI_CRAFT_SRC_GLOB`-style setting from the settings entry so the match pattern
   is per project.

## Risks / Trade-offs

- [DESIGN.md drifts from components as features evolve] → the token test catches token drift;
  the component inventory is a short list reviewed when `/ui-check` runs, and the skill tells the
  agent to update the inventory when it adds a primitive.
- [Two copies of the skill (kit and project) diverge] → README states the kit is upstream;
  `install.sh` is idempotent, so re-running it refreshes the project copy.
- [Reminder hook becomes noise] → it prints one line and only on frontend edits; it can be
  removed by deleting one settings entry.
- [`/ui-check` depends on a running dev server and a browser tool] → the command first tries the
  Playwright harness (no server needed) and falls back to `/run` plus Claude in Chrome; if neither
  works it reports which checks it could not run instead of passing them.
- [Deriving `DESIGN.md` for this project could invent rules the code does not follow] → the
  document is written from `index.css`, `components/ui/*` and the `web-ui-shell` spec, and every
  claim is checked against those files during implementation.

## Migration Plan

Additive only. Install the kit into this project with its own `install.sh`, then fill
`DESIGN.md` from the code. Rollback is deleting the new files and the two bullets in
`frontend/CLAUDE.md`.
