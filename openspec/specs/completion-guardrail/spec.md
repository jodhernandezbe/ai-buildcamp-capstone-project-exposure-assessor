# completion-guardrail Specification

## Purpose
TBD - created by archiving change naics-titles-and-full-coverage. Update Purpose after archive.

## Requirements

### Requirement: Opt-in completion check after the agent
The agent graph SHALL accept an optional completion check. When it is enabled, every reply the agent ends without tool calls SHALL be reviewed, using the injected chat model with a prompt loaded from the prompt files, against the latest message the user wrote: a reply that announces work the agent itself would do next (gathering inputs, computing results), asks whether to proceed, or narrows the scope on its own SHALL be judged not complete; a finished assessment, an explanation of why it cannot continue, an answer to a question, or a reply waiting for something only the user can give (a CAS number, a place, a choice) SHALL be judged complete. When it is not enabled, the graph SHALL behave exactly as before.

#### Scenario: Disabled by default
- **WHEN** the agent is built without a completion check
- **THEN** the graph's nodes, edges and model calls are unchanged from the current agent

#### Scenario: Complete reply
- **WHEN** the reviewer judges the reply complete
- **THEN** the turn ends with that reply and the model is not called again

#### Scenario: Waiting on the user
- **WHEN** the reply asks for a CAS registry number the user did not give
- **THEN** it is judged complete and the turn ends

### Requirement: A deferred reply is nudged back to work, a bounded number of times
A reply judged not complete SHALL be followed by a nudge, a user-role message carrying the guardrail's name and the configured nudge text, after which the agent SHALL run again with its tools. The nudges of one user turn SHALL be counted and SHALL NOT exceed the configured maximum; past it the reply stands as written. Nudges SHALL NOT appear in the thread's messages as the interface restores them, and SHALL NOT count as user messages for the scope check; the text written after a nudge joins the same assistant reply.

#### Scenario: Announced work
- **WHEN** the agent ends with "I will now gather stack, weather and population data"
- **THEN** it is nudged, calls its tools and finishes the assessment in the same turn

#### Scenario: Limit reached
- **WHEN** the agent has been nudged the configured number of times in this turn and ends early again
- **THEN** no further nudge is sent and the reply stands

#### Scenario: Hidden from the interface
- **WHEN** a thread that was nudged is restored
- **THEN** the nudge is not among its messages and the assistant text around it is one message

### Requirement: Reviewer failure lets the reply stand
When the reviewer cannot be reached, refuses, or gives no usable verdict, the reply SHALL stand as written (the check fails open), and the failure SHALL be logged without a traceback when it carries a provider status.

#### Scenario: Provider refusal
- **WHEN** the reviewer call fails with an HTTP status
- **THEN** the turn ends with the agent's reply and the log records the failure without a traceback
