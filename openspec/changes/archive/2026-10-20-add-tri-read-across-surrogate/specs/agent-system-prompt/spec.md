## ADDED Requirements

### Requirement: How an assessor treats a missing chemical
The prompt SHALL explain, as assessment reasoning and without naming a tool, the three ways a
chemical can be missing from the evidence and how each is treated: a chemical named without
a CAS registry number is not identified, so the user is asked for the number and none is
supplied; an identified chemical that is not on the TRI list or has no inhalation benchmark
may be estimated from a well-characterized chemical of similar structure (read-across), with
the similarity and its defensibility stated, the borrowed value never presented as measured,
and the gap reported when no defensible analogue exists; and an identified chemical absent
from the release inventory shows no reported releases, not that nobody emits it.

#### Scenario: Name without a CAS number
- **WHEN** the user asks for an assessment of a chemical by name only
- **THEN** the agent's reply is a request for the CAS number, it calls no tool and it writes no CAS number

#### Scenario: Borrowed value
- **WHEN** the prompt is read
- **THEN** it says a value taken from a structural analogue is an estimate, never a measured value for the chemical

### Requirement: The CAS rule stands on its own
The prompt SHALL state the rule that a chemical is identified only by a CAS number the user
has written as its own unconditional instruction, separate from the general instruction to
ask for anything essential that no tool can supply, and SHALL forbid writing a CAS number as
a suggestion, an example or something to confirm. The wording SHALL be the one measured
clean against the evaluation model, and an automated test SHALL pin it, because paraphrases
of the same rule were measured to change the model's compliance.

#### Scenario: Rule pinned
- **WHEN** the CAS rule's wording is changed
- **THEN** the prompt test fails until the new wording is measured and pinned

## MODIFIED Requirements

### Requirement: Output format and structure
The prompt SHALL ask for a short summary, per-facility results with units, ranges and the origin of each input, plain-language comment on results beyond a health benchmark, and a Limitations section listing the method's limits, defaults or generic inputs and data gaps, and SHALL be structured with the `role`, `context`, `instructions` and `output_format` XML tags in that order. When the assessment cannot start because something only the user can give is missing, the prompt SHALL ask for a reply containing just that request and why it is needed, not the report format.

#### Scenario: Structure
- **WHEN** the prompt is loaded
- **THEN** it contains the four tags in that order

#### Scenario: Nothing to report yet
- **WHEN** the assessment cannot start because the user has not given the chemical's CAS number
- **THEN** the reply is the request alone, with no summary, results table or Limitations section
