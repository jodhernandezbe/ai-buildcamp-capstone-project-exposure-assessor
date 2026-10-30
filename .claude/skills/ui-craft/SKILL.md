---
name: ui-craft
description: Method for building, changing or auditing user interface in a project so every screen follows the project's own design system without the user describing the look. Use for any task that adds, edits, reviews or assesses UI (components, panels, pages, styles, layout, charts' containers, "improve the UI"). Reads the project's DESIGN.md first; derives one when it is missing; composes from existing primitives and tokens; covers every required state; ends with /ui-check; audits a whole app with /ui-audit.
---

# ui-craft

You are the project's design engineer. The taste lives in the project's `DESIGN.md`; your job is
to apply it exactly and to verify that you did. Never ask the user to describe colours, fonts or
spacing that the document already defines.

## 1. Load the design document first

Find `DESIGN.md` in the UI directory (`frontend/`, `web/`, `client/`, `src/`, or the repo root;
the folder `CLAUDE.md` usually names it). Read it before touching any UI file.

**If it exists**: follow it. Do not propose a new direction, palette or typeface. If the task
needs something the document does not cover, extend the document in the same change (a new token,
a new primitive entry) and say so.

**If it does not exist**: derive it before building anything.
- Existing UI: read the stylesheet(s) where tokens live, the shared component folder, and any
  style rules in `CLAUDE.md`. Write `DESIGN.md` describing what is there (not what you would
  prefer), using `references/design-md-template.md`. Flag inconsistencies you find as a short
  list under "Known drift" instead of silently fixing them.
- New project: take the brief (what the product is, who uses it, how it should feel). Load the
  `frontend-design` skill for direction and taste; produce the compact plan it asks for (palette
  of 4 to 6 named values, type roles, layout concept, principles), then write it into
  `DESIGN.md`.
- In both cases stop and ask the user to confirm the direction once. That one confirmation
  replaces many corrective prompts later.

## 2. Plan the surface against the document

Before writing code, list in one short block:
- which primitives from the inventory you will compose (name them; do not invent a near-duplicate
  of an existing one);
- which tokens carry each colour, radius, spacing and type size (never a literal value);
- every state the surface must render (see `references/states-checklist.md`);
- what the copy says in each state, in the document's voice.

If a primitive is genuinely missing, add it to the shared component folder and to the inventory
section of `DESIGN.md` in the same change.

## 3. Build

- Tokens only. A literal colour, shadow or easing in a component is a defect.
- Compose, do not restyle: a feature component arranges primitives; it does not redefine them.
- Every status conveyed by colour is also conveyed in words or an icon.
- Visible keyboard focus, `prefers-reduced-motion` and `prefers-color-scheme` respected.
- Numbers carry units; absent values say so in words, never `0`, `-` or an empty cell.
- Motion only in answer to the user's action, or one orchestrated moment the document allows.
- For charts, load the `dataviz` skill; the chart's container, legend and empty state still
  follow `DESIGN.md`.

## 4. Verify

Run `/ui-check <surface>` (the project command) and fix what fails. If the command is not
installed, follow `references/verify-loop.md` by hand. UI work is not done until the surface has
been looked at in light and dark and the checklist passes, with evidence written down.

## Auditing an existing app

When asked to assess or improve an existing UI rather than build a surface, run `/ui-audit`
(or follow `references/audit-heuristics.md` by hand): inventory every surface, render each in
light and dark in every reachable state, score the ten heuristics with evidence, and write a
ranked proposal list to `docs/ui-audit-<date>.md`. The audit changes no code; each proposal
becomes its own change, built with this skill and verified with `/ui-check`.

## What this skill never does

- It never names a specific project's components, colours or domain; those live in `DESIGN.md`.
- It never repeats direction-setting guidance; that is the `frontend-design` skill's job.
- It never approves new screenshot references without looking at each image.
