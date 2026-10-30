## Context

See proposal.md and `docs/ui-audit-2026-10-30.md`. All nine items are frontend-only and small;
the audit found the causes:

- `EpaOverviewRibbon` uses `auto-rows-[minmax(max-content,1fr)]`, so the first row (worst-case
  section) gets a share of the panel even when it holds one sentence.
- `SplitWorkspace` covers the analysis area at `z-10`; the map's basemap button is `z-20`, so it
  wins. `PanelFrame` fullscreen is `z-30`.
- `MapLegend` always renders counts; `SessionsTable` has a `min-w-[56rem]` table in an
  `overflow-x-auto` box whose scrollbar is invisible on macOS.
- `SettingsDrawer` already opens the Assistant section when the OpenAI key is missing; when the
  key is saved both sections are collapsed and silent.
- `LeftNavRail` `Item` already puts the reason in `title`; it lacks an accessible description.
- `BrandLogo`'s `CompartmentPill` renders "AIR • WATER • SOIL".
- `FlowEdge` labels are 9 px and 10 px. `DemographicsCard` maps a missing band to `0`.

## Goals / Non-Goals

**Goals:** fix the nine findings with the smallest change each, keep every existing behaviour
the specs require, verify each surface with `/ui-check`, update `DESIGN.md` with the four rules.

**Non-Goals:** no new primitives, no restyle, no change to data or API, no CI changes.

## Decisions

1. **Empty first row via an explicit `grid-rows-[auto]` when there are no scenario drivers.**
   `grid-template-rows: auto` sizes only the first explicit row; implicit rows keep
   `grid-auto-rows`. Alternative: render the empty section outside the grid; rejected because it
   changes the DOM order the tests and the container query rely on.
2. **Map isolation with `isolate` on the map root** rather than raising the covering layer's
   z-index: it fixes the class of bug (any future map overlay) and leaves the z ladder
   (content < overlays inside their region < covering `z-10` < fullscreen `z-30` < drawers) intact.
   Documented in `DESIGN.md`.
3. **Legend: one sentence when `facilities.length === 0`**, entries still rendered (toggles keep
   working) but without the count span, plus the sentence. Alternative: hide the legend; rejected
   because the legend explains marker colours before the first pin appears.
4. **Sessions table: fixed layout plus container query tiers, not horizontal scroll.** A first
   attempt (hide four columns under `@4xl`) still overflowed at every width when measured live:
   the question column and unwrapped headers kept the table wider than the pane. Final: `table-fixed`
   with set widths for every column except the question (which truncates, tooltip kept); model and
   turns from `@3xl`, the counts, tokens and duration from `@7xl`; headers may wrap. Measured with
   Playwright at 1280, 1440 and 1920 px: no overflow. Header names stay as they are (already
   distinct; the audit saw "Model" beside a cut "Model calls").
5. **Accordion gets an optional `summary` node** shown right-aligned in the heading button;
   `SettingsDrawer` passes "Key saved" / "Key missing" (or "n of m keys saved") in `text-fg2`.
6. **Rail: `aria-description={blocked}`** on the button; React 19 passes it through.
7. **Compartment pill: words, sentence case,** "Air" in accent, "Water (planned)", "Soil
   (planned)" in `text-fg2`, separated by spacing only.
8. **Edge labels 11 px / 12 px;** re-approve the ten exposure-chain references after looking.
9. **Demographics: only bands present** go to `SegmentedBar`; missing ones are listed in a
   `text-xs text-fg2` line "Not reported: 0-4, 65+".

## Risks / Trade-offs

- [Screenshot references change for the chain] → look at every new image before `-u`.
- [Container query breakpoint hides columns on medium panes] → `@4xl` (56 rem) matches the
  table's previous minimum width, so nothing hides that used to fit.
- [`isolate` changes stacking of the inspector popovers inside the map] → they are children of
  the map root and keep their relative order; verified by the map tests and a live look.
