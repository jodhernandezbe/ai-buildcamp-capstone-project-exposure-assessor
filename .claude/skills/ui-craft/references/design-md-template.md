# Writing a project's DESIGN.md

Use `templates/DESIGN.template.md` from the kit (or the copy the installer left at the UI
directory) as the skeleton. These notes say what goes in each section and what to avoid.

## Sections, in order

1. **Direction** (3 to 6 sentences). What the product is, who looks at it, and the one idea the
   visual language serves (for example "a lab instrument: quiet surfaces, numbers first,
   status in words"). Name the typeface(s) and their roles. Name the memorable element and say
   that everything else stays quiet.

2. **Tokens**. One table: `--token` in backticks, light value, dark value, meaning, allowed use.
   Every token the stylesheet declares in its light theme block must appear here, and nothing
   that the stylesheet does not declare. The `designDoc.test.ts` template enforces exactly this.
   Group semantically (surfaces, text, lines, accent, status, series, effects, type).

3. **Type and spacing scale**. The handful of sizes, weights and spacings actually used, each
   with its role (caption, label, body, metric, title). Fewer rows than you think; if the code
   uses twelve sizes, list the ones that are intended and put the rest under "Known drift".

4. **Materials, radius and motion**. Surface treatments (solid, translucent, hairline), the
   radius ladder and what each step is for, shadows, the easing curve, durations, and the rule
   for when motion is allowed.

5. **Primitives**. One line per shared component: name, what it is, when to use it, when not to.
   This is the list the agent composes from. Keep it current: adding a primitive means adding a
   line here.

6. **Required states**. The states every data surface renders (loading, empty, absent value,
   error, success or ready, stale). For each: how it looks and what it says. See
   `states-checklist.md`.

7. **Copy**. Voice, capitalisation, how units and numbers are written, the exact words for
   absent and unknown values, how errors are phrased.

8. **Anti-patterns**. Short list of things that look right but are wrong here (literal colours,
   colour-only status, numbered markers on non-sequences, all-caps labels if the direction
   forbids them, decorative motion).

9. **Known drift** (optional). Places where the code does not yet match the document, so the
   agent does not copy them.

## Rules of thumb

- Describe the UI as it is meant to be; never restyle while documenting an existing project.
- Prefer rules with a reason ("hairlines, not shadows, separate regions because the surfaces
  are translucent") over bare preferences.
- Short. A page or two. If a section grows past a screen, it belongs in a reference file.
- Markdown headings exactly as in the template: the command and the test look for `## Tokens`
  and `## Required states`.
