# The verification loop

Do this after every UI change, before calling the work done. The `/ui-check` command automates
the steps; this is the manual version.

## 1. Render in both colour schemes

Pick the cheapest tool that works, in this order:

1. **Screenshot test harness** (Vitest browser mode with Playwright, or similar). No dev server
   needed; renders the component with fixtures in light and dark and compares with approved
   references. Run it. New or changed images must be opened and looked at before approving them.
2. **Live app**: start the dev server (the project's `/run` skill or its documented command),
   open the surface with the browser tool available (Claude in Chrome, Playwright MCP, built-in
   browser), take one screenshot per colour scheme. Toggle the scheme with the browser's
   emulation or the OS setting; do not add a theme switch to the app for this.
3. **Neither available**: say so. Report the checks you could not run as "not run", never as
   passed.

## 2. Check against DESIGN.md

For the surface in each screenshot, go through:

- Every colour, radius, shadow and type size is a documented token or scale step.
- Each state in the required-states table is reachable and looks as documented (render the
  empty and error states with fixtures, not only the happy path).
- Status is never colour alone.
- Focus is visible on every control; icon-only controls have names.
- Reduced motion stops non-essential animation.
- Numbers have units; absent values use the project's words.
- Copy follows the document's voice and casing.
- Nothing in the anti-patterns list is present.

## 3. Run the mechanical checks

- The project's lint, type and unit checks.
- The design document test (tokens documented and declared).
- The contrast test (token pairs meet WCAG AA).
- The screenshot test, approving only images you have looked at. A pixel tolerance (for
  example 1 %) absorbs small text changes, and `-u` rewrites only failing references: after a
  deliberate change to small text, delete that surface's references and regenerate them.
- For layout fixes, measure instead of trusting class names: in the browser, compare a
  container's `scrollWidth` with its `clientWidth` at the widths that matter.

## 4. Write the evidence

A short table: check, result (pass / fail / not run), evidence (screenshot name, test name, line).
Fix every fail and run the loop again. The table, not a sentence, is what "verified" means.
