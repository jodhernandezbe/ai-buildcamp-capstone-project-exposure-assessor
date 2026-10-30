# Required states of a data surface

A panel, card, table or chart that shows data from somewhere else must render every state below,
and `DESIGN.md` says how each one looks in the project. Check them off when planning and again
when verifying.

| State | When | Must show | Must not |
| --- | --- | --- | --- |
| Loading | A request is in flight, no data yet | A quiet placeholder in the surface's final size and a status announced to assistive technology | A spinner that shifts layout; stale data presented as current |
| Empty | The request succeeded and there is nothing | One sentence saying there is nothing and, when useful, what would make something appear | A blank area; a zero that could be read as a value |
| Absent value | A record exists but a field is missing | The project's exact words for "not reported" (or the reason given by the source) | `0`, `-`, `N/A`, an empty cell |
| Error | The request failed | What failed in plain words and what the user can do; announced to assistive technology as an alert | A raw exception; colour alone; an error that disappears before it can be read |
| Ready | Data present | Numbers with units, status in words plus colour, provenance when the source matters | Colour-only status; unitless metrics |
| Stale or partial | Data is older than the current input, or a stream is still arriving | A visible marker that it is partial or older | Silent mixing of old and new |
| Interactive | The surface has controls | Visible focus, pressed and disabled states, labels for icon-only controls | Hover-only affordances; controls without an accessible name |

## Quick verification questions

- Can I tell loading from empty from error with the screen in greyscale?
- Does every absent value use the project's words for it?
- Does every metric carry a unit, and is the number of digits the configured one?
- Can I operate the surface with the keyboard alone, and do I always see where I am?
- Does anything move without me asking it to, and does it stop under `prefers-reduced-motion`?
- Is any colour, radius, shadow or font size a literal rather than a token?
