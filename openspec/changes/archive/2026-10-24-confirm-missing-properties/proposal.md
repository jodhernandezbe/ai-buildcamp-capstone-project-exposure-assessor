## Why

Today, when a chemical benchmark cannot be found, the assessment silently
carries a null with a warning and the user never learns that a value is missing or gets a
chance to supply it. A facility or chemical with an incomplete record produces a result that is
either weaker than it could be or quietly narrower, and the user has no way to fill the gap
from what they know (for example, an inhalation unit risk from a study that CompTox does not hold). The agent should tell the user what is missing and ask: proceed
without the value, or enter it so it is used in the analysis.

## What Changes

- When the agent finds that a value the analysis needs is missing, it SHALL stop and tell the
  user which values are missing and why each one matters for the result.
- The user is offered two choices per missing value: **proceed without it** (the value stays
  absent, the warning stays, nothing is guessed) or **enter a value** with its unit.
- The request is shown as a card in the chat thread with a **Confirm** button. Each entry has a
  numeric input and a unit selector limited to units of the same quantity; the unit of the
  field is always visible. Free text is not used for values.
- User-entered values are converted to the documented target unit with the project's unit
  conversion, checked against the plausible range configured for that quantity, and rejected
  with a reason when they fail (never clipped or coerced).
- Entered values are used by the analysis and labelled as user-provided wherever the source of
  a value is reported (the same way toxicity values passed in as "given" are labelled today).
- The pending request belongs to the chat thread: it survives reloads, and a message that
  ignores the card counts as "proceed without" for each open item.
- **BREAKING** (for the chat API): the turn stream gains a new event type for the confirmation
  request, and a turn may carry the user's answers instead of a text message.

## Capabilities

### New Capabilities
- `missing-value-confirmation`: detecting missing inputs that change the result, asking the user
  for each one, validating and converting entered values, and labelling their provenance.

### Modified Capabilities
- `web-ui-server`: new turn event for the confirmation request and a reply form that carries
  the user's answers (the chat contract and generated schema change with it).
- `agent-system-prompt`: the reasoning the agent follows when a needed value is missing (ask
  once, in one message, before concluding) without naming tools or a call order.
- `chemical-properties-tool`: a property the user supplied is accepted as a source for that
  field, and the source label reports it.

## Impact

- `agent/`: a stop-and-ask path in the graph that ends the turn with a pending request, and
  resumes from the user's answers on the next turn.
- `tools/`: optional user-supplied values for the chemical benchmarks `rfc` and `iur`
  (`tools/informatics/properties.py`, `tools/schemas.py`), with the provenance label.
- `commons/units.py`: reused for conversion; no change expected unless a unit alias is missing.
- `config/settings.toml`: accepted units and plausible ranges for the chemistry quantities.
- `api/`: new SSE event schema, a reply form on the chat request, thread-scoped pending state.
- `frontend/`: a confirmation card in `features/chat/` with numeric inputs, unit selectors and
  Confirm / proceed-without controls; generated types in `frontend/src/types/`.
- `prompts/agent_system.md` and its tests.
- Evals: a scenario with a missing property and a cassette for the confirmation turn.
- No change to the models layer; equations are untouched.
