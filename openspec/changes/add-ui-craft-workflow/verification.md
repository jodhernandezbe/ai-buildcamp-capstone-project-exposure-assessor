# /ui-check: Overview ribbon (`features/overview/EpaOverviewRibbon`)

Run on 2026-10-30 as task 4.1, following `.claude/commands/ui-check.md`.

Render: Playwright Chromium through `vitest.visual.config.ts`, light and dark projects, new
`EpaOverviewRibbon.visual.tsx` with two states (empty workspace; ready with synthetic round
numbers). References under `features/overview/__screenshots__/EpaOverviewRibbon.visual.tsx/`,
each of the four images opened and looked at before approval.

| Check | Light | Dark | Evidence |
| --- | --- | --- | --- |
| Tokens only (no literal colour, shadow, easing, font) | pass | pass | grep of `features/overview`, `components/ui`, `components/layout` for `#hex`, `rgb(`, `hsl(`, `cubic-bezier`, `font-family`, `box-shadow`: no hits outside `BrandLogo` |
| Required states present | pass | pass | `ribbon-empty-*`: "Not computed" pills, "not reported" slots, "Not shown: not yet computed." reasons, "No scenario yet…" empty sentence; `ribbon-ready-*`: values with units |
| Colour never the only cue | pass | pass | Pills read "Above concern", "Near concern", "Not computed", "Not reported" beside their tint |
| Focus visible | pass | pass | Ribbon has no interactive controls; focus ring rule is global (`:focus-visible`, `index.css`) |
| Reduced motion respected | pass | pass | Ribbon has no animation; global rule collapses durations |
| Numbers with units, absent values in words | pass | pass | `2.5`, `0.4` (unitless, labelled), `1.2 × 10⁻⁵`, `50 g/mol`, `0.5 mg/m³`; every absent value "not reported" |
| Copy voice | pass | pass | Sentence case; uppercase only on card titles (`CardFrame`), now documented in `DESIGN.md` |
| No anti-pattern | pass | pass | No numbered markers, no decorative motion, no hard-coded thresholds; digits from the `digits` prop |
| Design document test (`designDoc.test.ts`) | pass | | 15 tokens declared = 15 documented |
| Contrast test (`contrast.test.ts`) | pass | pass | 26 pairs ≥ 4.5:1 |
| Screenshot test (`test:visual`) | pass | pass | 16 tests across 4 files, including the 4 new ribbon references |

Result: verified in both colour schemes. No `fail` rows.

Observations (not failures, for a later decision):
- With no scenarios, the worst-case section still occupies a full grid row (one sentence in a
  band about a third of the panel). The code comment says rows grow on purpose so a fullscreen
  overview is large cards rather than a strip; an empty section could instead collapse to
  `max-content` until it has content.
- `DESIGN.md` first claimed uppercase appeared only in `PanelHeader`; the screenshots showed
  card titles are uppercase too (`CardFrame`). Corrected in the document during this check.
