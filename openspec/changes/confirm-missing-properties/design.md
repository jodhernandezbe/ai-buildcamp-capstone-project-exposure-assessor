## Context

See proposal.md - Why. Today every data layer already fails closed: a missing value is None with a
warning (chemical properties, stack parameters, RfC/IUR in `tools/exposure/metrics.py`), and
the agent is told never to fill a gap. Nothing asks the user. The chat is one HTTP turn per
message (`api/routers/v1_chat.py`) streamed as typed events (`api/schemas/chat.py`), with a
LangGraph checkpointer per thread (`agent/graph.py`, `threads.py`). There is no
human-in-the-loop interrupt yet. The existing precedent for user-supplied numbers is
`assess_facilities(toxicity=...)`, where the model passes `rfc`/`iur` as tool arguments; that
carries the value through the model's own copying, which is the weak point for units.

## Goals / Non-Goals

**Goals:**
- Ask once per turn for every missing value that changes the result, and let the user either
  proceed without it or enter it in a validated unit.
- Keep the fail-closed rule: nothing is guessed, clipped or defaulted, and every supplied value
  is labelled user-provided.

**Non-Goals:**
- Asking about meteorology or population inputs. They already fall back to documented screening
  defaults with a warning; changing that is a separate decision.
- Asking for CAS numbers (the prompt's CAS rule stands).
- Changing any equation in `models/`, or the RAG and SCC retrieval.

## Decisions

### D1. Confirmation card with buttons, not free text
The request is a structured event rendered as a card in the chat thread. Each entry has a
numeric input, a unit selector limited to the same quantity, the target unit visible, and two
choices: **Confirm** (value) or **Proceed without**. The agent's message still states the missing
values in prose so the transcript reads on its own.
- Alternative: free text ("the vapor pressure is 12 mmHg"). Rejected as the primary path: the
  model would have to parse value, unit and field from prose, and a wrong unit silently becomes a
  wrong number. Free text remains the behaviour if the card is not shown (for example, an old
  client): the agent asks in prose, and a reply that does not answer the request is treated as
  proceed without (see D5).

### D2. The turn ends at the request; answers arrive as the next turn's input
The graph stops after the model writes the request (no interrupt, no held connection). The
open request is stored with the thread. The browser posts the answers as a turn input naming the
request id; the server validates them, stores the accepted values with the thread, and starts the
next turn.
- Alternative: LangGraph `interrupt()` with a resume call. Rejected for now: it keeps a run
  paused across HTTP requests and needs the runner's cancellation and busy-thread logic
  (`threads.claim/release`) to change. The end-and-resume shape reuses the existing turn route.

### D3. Given values are injected by the runner, not carried by the model
Accepted values live in thread state (next to the checkpointed messages) and are handed to the
tools by the runner, the way the thread's workspace is already kept server-side
(`api/services/threads.py`). The model is told which values exist through a short system note
generated from that state, and never has to copy a number into a tool call.
- Alternative: pass the values as tool arguments, as `assess_facilities(toxicity=...)` does.
  Rejected for new fields: it puts unit conversion in the model's hands, and the model can drop
  or alter a value. Keep the existing `toxicity` argument as it is.
- Tools stay free of `api` imports: the injected value is a plain typed mapping passed through
  the tool's config or state port defined in `tools/schemas.py`.

### D4. Units and validation
- Each entry offers a short list of accepted units configured in `config/settings.toml`, one list
  per quantity; the first is the target unit. Examples: vapor pressure mmHg (also torr, Pa, kPa,
  atm, hPa); molecular weight g/mol; density g/cm^3 (also kg/m^3); RfD and RfC in their configured
  targets; stack height m (also ft); diameter m (also ft, in); exit velocity m/s (also ft/s); exit
  temperature K (also degC, degF).
- Conversion uses `commons/units.convert` (Pint). Temperatures must be converted as absolute
  temperatures; 25 degC becomes 298.15 K, never a difference.
- Reciprocal units (SF, IUR) are converted through Pint like any other unit; the 1000-fold
  difference between (ug/m3)^-1 and (mg/m3)^-1 is covered by a negative test.
- Validation order: finite number, not a boolean, converts exactly, inside the plausible range.
  Plausible ranges already exist for stack quantities (`[stack.ranges]`); the same mechanism is
  added for chemistry quantities. Failures return a reason and keep the entry open.

### D5. Open requests and new messages
An open request is kept in the thread across reloads. If the user sends a new message instead
of answering, each open entry is recorded as proceed without, and the agent says so in its reply.
This means the agent never waits on an answer that is not coming.

### D6. Provenance
A user-supplied value is labelled `user-provided` in every place that reports a source: the
chemical properties `sources` map (new label, as a delta in the chemical-properties spec) and
`stack_source` for stack parameters (new value next to "NEI", "PSTK" and the EPA global default).
The final report says which values came from the user.

### D7. Where the missing check lives
The check is a small function after the tools have run: it reads the warnings and the nulls
that change the requested result, and builds the request. It does not decide the result itself.
The prompt says when to ask (the agent reasons about it); the code decides what counts as missing
for the requested result. This keeps the prompt free of tool order, as the prompt spec requires.

## Risks / Trade-offs

- [Asking too often makes the assessor tiresome] → Ask only for values that change the requested
  result; batch them into one request; tests cover the "does not change the result" case.
- [A stale request blocks a conversation] → D5: a new message closes open entries as proceed
  without, and the agent says so.
- [Unit mistakes give plausible-looking wrong numbers] → Fixed target unit visible on the entry,
  server-side re-validation (never trust the browser), negative tests for temperature offset and
  reciprocal units, and range checks.
- [Model text and card disagree] → The card is built from the same request record the agent
  wrote; the prose lists the same fields, and a test compares them.
- [The provenance and missing-value requirements in the existing specs are extended by ADDED
  deltas rather than MODIFIED ones] → Acceptable for this change; when archiving, fold the new
  "user-provided" source into the existing "Provenance of values" requirement so the main spec
  reads as one requirement.
- [Evaluation drift] → The eval harness uses recorded tool outputs; a new scenario and cassette
  cover the confirmation turn. Prompt changes need the repeated eval runs noted in project memory.

## Migration Plan

No data migration. Threads without open requests behave as before. The chat contract gains an
event type and a reply form; the generated schema and `frontend/src/types/` are regenerated in
the same change. Rollback is removing the stop-and-ask node and the card; tools keep accepting
their current arguments, so no stored data needs conversion.

## Open Questions

- Which exact accepted-unit list per quantity the user wants (the list above is a starting point).
- Whether the card should also appear for missing toxicity benchmarks, or only for chemistry and
  stack inputs. The proposal assumes chemistry and stack inputs; RfC and IUR count as chemistry
  here because the RfC/IUR chain already reports them as missing.
