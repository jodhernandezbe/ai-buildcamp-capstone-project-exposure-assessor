---
description: Audit every UI surface against DESIGN.md and the audit heuristics; produce a ranked improvement proposal without changing code
argument-hint: [surface filter or "all"]
---

Audit the user interface of this project. Scope: `$ARGUMENTS` (empty or "all" means every
surface). Load the `ui-craft` skill if it is not loaded, then read
`references/audit-heuristics.md` and the project's `DESIGN.md` (if there is none, derive it first
as the skill says and stop for confirmation; the audit needs a reference).

The audit changes no application code. Its only outputs are screenshots (in the scratch
directory or the test harness) and the report.

Steps:

1. **Inventory the surfaces.** List every screen, panel, card, drawer, dialog and chat view from
   the feature folders and the shell. One row per surface with its file(s) and the states it can
   be in. Include the empty state of the whole app (first load) as a surface of its own.

2. **Render each surface in light and dark, in as many states as you can reach.** Cheapest
   first: approved screenshot references from the test harness; then the live app (project `/run`
   skill or documented dev command) through the available browser tool, with scheme emulation;
   then fixtures through a temporary visual test that is deleted afterwards. Use realistic data
   when it is available (recorded cassettes, demo fixtures); never invent values that look real.
   Name each screenshot `<surface>-<state>-<scheme>`.

3. **Score each surface** on the ten heuristics (0, 1, 2) with evidence per score. Also run the
   static checks from `/ui-check` across the UI source: literal values, colour-only cues,
   unnamed icon controls, zero or dash for absent values, hard-coded display settings.

4. **Write proposals** for every heuristic scored below 2 following the heuristics reference:
   observation, evidence, smallest change, design document impact, effort, value. Merge proposals
   that share one root cause into one.

5. **Write the report** to `docs/ui-audit-<YYYY-MM-DD>.md` (create `docs/` if missing; inside an
   OpenSpec change, write it to the change folder instead) with these sections: Scope and method
   (tools used, states reached, states not reached); Scoreboard (one row per surface, ten scores,
   total); Ranked proposals (top first, numbered, each with the six fields); Design document
   changes (the consolidated list); Not assessed (surfaces or states you could not render and
   why). End with the three proposals you would do first and why.

6. **Report back** with the scoreboard and the top three proposals. Do not implement anything:
   each proposal becomes its own change, built with the `ui-craft` skill and verified with
   `/ui-check`.
