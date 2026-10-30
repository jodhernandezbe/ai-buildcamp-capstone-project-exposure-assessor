---
description: Verify a changed UI surface against DESIGN.md in light and dark, with evidence
argument-hint: <surface or component name>
---

Verify the UI surface `$ARGUMENTS` (if empty: every surface touched by the current working tree
changes under the UI directory) against the project's design document. Load the `ui-craft` skill
if it is not loaded.

Steps:

1. **Locate**. Find `DESIGN.md` (UI directory named in the folder `CLAUDE.md`; otherwise look in
   `frontend/`, `web/`, `client/`, `src/`, repo root). Read its Tokens, Required states, Copy and
   Anti-patterns sections. List the files of the surface (`git diff --name-only` plus the
   argument).

2. **Render light and dark**, cheapest tool first:
   a. If the project has a screenshot test config (for example `vitest.visual.config.ts`), run it
      for the surface; if the surface has no `*.visual.tsx`, write one with fixtures that reach
      the ready, empty, absent-value and error states, then run it. Open every new or changed
      image and look at it. Approve references (`-u`) only after looking at each image.
   b. Otherwise start the app (project `/run` skill or its documented dev command) and open the
      surface with the available browser tool; capture one screenshot per colour scheme using
      the browser's scheme emulation.
   c. If neither works, continue with the static checks and mark the visual rows "not run".

3. **Static checks**. Grep the surface's files for literal colours (`#`, `rgb(`, `hsl(`), literal
   shadows, easing curves and font sizes that are not tokens or documented scale steps. Confirm
   each status element also carries words or an icon. Confirm icon-only controls have names.

4. **Mechanical checks**. Run the project's lint, type and unit checks for the UI package, the
   design document test and the contrast test if present, and the screenshot test from step 2a.

5. **Report** a table with one row per item, columns: check, light, dark, evidence. Items:
   tokens only; required states present; colour never the only cue; focus visible; reduced motion
   respected; numbers with units and absent values in words; copy voice; no anti-pattern; design
   document test; contrast test; screenshot test. Results are `pass`, `fail` or `not run`. Name
   the component and file for each fail.

The surface is verified only when no row is `fail`. Fix fails, re-run, and keep the final table
in the response (and in the change folder when working inside an OpenSpec change).
