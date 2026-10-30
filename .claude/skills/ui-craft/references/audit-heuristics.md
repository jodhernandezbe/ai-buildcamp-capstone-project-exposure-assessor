# Audit heuristics

Used by `/ui-audit` to score every surface of an app. Each heuristic is scored 0, 1 or 2 per
surface, with the evidence (screenshot name or file and line) written next to the score.

| # | Heuristic | 2 (good) | 1 (partial) | 0 (poor) |
| --- | --- | --- | --- | --- |
| H1 | **Hierarchy**: the eye lands on the most important value first | One clear primary element; secondary content visibly quieter | Primary element present but competes with chrome or equals | Everything the same weight, or chrome louder than data |
| H2 | **Density and rhythm**: spacing follows the scale, nothing cramped or stranded | Consistent gaps from the scale; no large dead bands or truncation | One cramped or stranded region | Several, or layout breaks at a common width |
| H3 | **System consistency**: uses the documented primitives and tokens | Composes from the inventory; tokens only | One near-duplicate primitive or an undocumented step | Literal values or ad-hoc components |
| H4 | **States**: every required state is reachable and intentional | Loading, empty, absent, error, ready all designed | One state missing or generic | Several missing; blank or zero stands in for absence |
| H5 | **Status legibility**: meaning survives without colour | Words or icons always accompany colour; contrast passes | One colour-only cue | Colour is the only cue in several places |
| H6 | **Accessibility**: operable and announced | Names on all controls, visible focus, live regions for async, keyboard works | One missing name or unannounced change | Keyboard trap, unnamed controls, no announcements |
| H7 | **Copy**: says what it means in the project's voice | Plain words, units, reasons for absence, no jargon or raw errors | Minor inconsistency in casing or terms | Technical or ambiguous labels, raw errors |
| H8 | **Motion and feedback**: motion answers actions, actions get feedback | Every action gives feedback; nothing moves unprompted; reduced motion honoured | One silent action or one decorative movement | Decorative motion or actions with no response |
| H9 | **Resilience**: behaves when data is partial, long, or slow | Long text, many items, slow responses handled | One overflow or slow-state gap | Breaks with realistic data |
| H10 | **Fit to task**: the surface answers the user's question at that moment | The surface's purpose is obvious and the next step is clear | Purpose clear but next step not | Purpose unclear |

Score a surface out of 20. Use the scores to rank, not to grade people.

## Turning scores into proposals

For every heuristic scored 0 or 1, write one proposal with:

- **Surface and heuristic** (for example "Overview ribbon, H2").
- **Observation** with evidence (screenshot name, file and line).
- **Proposal**: the smallest change that moves the score to 2.
- **Design document impact**: none, or the token, primitive or rule to add or change.
- **Effort**: S (one component, under an hour), M (one feature), L (cross-cutting or new primitive).
- **Value**: how many surfaces or users it affects.

Rank by value over effort. The top items become proposals (one change each), implemented with
the `ui-craft` skill and verified with `/ui-check`. The audit itself changes no code.
