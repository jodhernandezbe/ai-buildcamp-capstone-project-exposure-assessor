## ADDED Requirements

### Requirement: Confirmation request event
The chat turn stream SHALL carry a typed event that presents an open confirmation request:
the thread it belongs to, a request identifier, and one entry per missing value with its field
name, chemical or facility, the units the entry accepts (the target unit first), and the
plausible range. The event SHALL be sent before the turn finishes, and the turn SHALL end
after it without an answer being required to close the stream.

#### Scenario: Turn ends with an open request
- **WHEN** the agent stops to ask about missing values
- **THEN** the stream sends the confirmation request event, then the turn-finished event, and the request remains open in the thread

#### Scenario: Event shape matches the wire contract
- **WHEN** the event is serialized
- **THEN** it validates against the published schema, and the frontend types are regenerated from that schema

### Requirement: Answers as a turn input
A chat turn SHALL be able to carry the user's answers to an open confirmation request in place
of a text message. The answers SHALL name the request identifier and give, for each entry,
either proceed without or a numeric value with its unit. The server SHALL validate the
answers against the open request and reject answers for a request that is closed, belongs to
another thread, or does not list the entry.

#### Scenario: Valid answers start the next turn
- **WHEN** the user confirms an open request with one value and one proceed without
- **THEN** the turn runs with those answers, and the answered entries are no longer open

#### Scenario: Answers for a closed request
- **WHEN** answers arrive for a request that was already answered
- **THEN** the server rejects the turn with a clear error and changes nothing in the thread

#### Scenario: Answers for an entry not in the request
- **WHEN** answers name a field that the open request does not list
- **THEN** that answer is rejected and the request stays open

### Requirement: Values are validated on the server
The server SHALL validate every entered value against its entry's accepted units and plausible
range before any tool runs, using the same rules as the frontend. The frontend check is for
convenience only and SHALL NOT be the only check.

#### Scenario: Browser sends a value the server rejects
- **WHEN** an answer carries a value outside the plausible range, even though the browser allowed it
- **THEN** the server rejects the answer, reports the reason, and keeps the request open
