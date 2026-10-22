# agent-system-prompt Specification

## Purpose

The system prompt that teaches the agent how an exposure assessor reasons, so that it decides what to do from the task, the tool descriptions and the tool results, and keeps working when tools are added or changed.

## Requirements

### Requirement: The prompt teaches the assessment, not the tools
The system prompt SHALL describe the process of an exposure assessment (the chain from chemical and sources through transport and receptors to exposure and risk, the quality of evidence, screening conservatism and uncertainty) and how to decide from results. It SHALL NOT name any tool and SHALL NOT prescribe an order of calls. An automated test SHALL fail when the prompt contains the name of a registered tool or a numbered list of steps.

#### Scenario: A tool name appears
- **WHEN** the prompt contains the name of a registered tool
- **THEN** the test fails and names the tool

#### Scenario: A new tool is registered
- **WHEN** a tool is added to the registry
- **THEN** the prompt needs no change for the agent to be able to use it

#### Scenario: A step list is added
- **WHEN** the prompt contains a numbered list of steps
- **THEN** the test fails

### Requirement: Decisions come from tool descriptions and results
Every tool description SHALL state what the tool is for and when it applies (including any condition on using it, such as only after a better source returned nothing), what each output means, what a null value, a `source` or a `warnings` entry implies, and what situation calls for a different tool. The prompt SHALL tell the agent to rely on these descriptions and to read each result critically before using it.

#### Scenario: A fallback tool
- **WHEN** the description of a tool that is a fallback is read
- **THEN** it says under what condition to use it and what its output does not represent

#### Scenario: Quality signals
- **WHEN** the description of a tool that can return a default is read
- **THEN** it says how a default is labelled and that the agent must report it

### Requirement: Evidence quality, alternatives and honesty
The prompt SHALL state that facility-specific evidence is preferred over process-typical and that over generic defaults, that a more generic source is used only when a better one is unavailable and is then disclosed, that several credible alternatives are each evaluated and reported as a range, that worst-case and typical results are both reported, that numbers, names and identifiers are never invented, estimated or converted by the agent (a chemical is called by the name a tool result gives, else by its CAS number alone), that a branch with no defensible answer is stopped with the reason, and that the user is asked when something essential and not obtainable by a tool is missing.

#### Scenario: Default in the data
- **WHEN** the prompt is read
- **THEN** it requires the final answer to say which inputs were defaults or generic and why

#### Scenario: Alternatives
- **WHEN** the prompt is read
- **THEN** it says to evaluate every credible alternative and report the range

#### Scenario: Chemical without a name
- **WHEN** the properties result carries no name for the chemical
- **THEN** the prompt requires the report to refer to it by its CAS number and never to supply a name

### Requirement: Output format and structure
The prompt SHALL ask for a short summary, per-facility results with units, ranges and the origin of each input named as the results name it (the source text of the weather, the residents, the stacks' tier and the toxicity benchmarks), plain-language comment on results beyond a health benchmark, and a Limitations section listing the method's limits, defaults or generic inputs and data gaps, and SHALL be structured with the `role`, `context`, `instructions` and `output_format` XML tags in that order. When the assessment cannot start because something only the user can give is missing, the prompt SHALL ask for a reply containing just that request and why it is needed, not the report format.

#### Scenario: Structure
- **WHEN** the prompt is loaded
- **THEN** it contains the four tags in that order

#### Scenario: Sources as the results give them
- **WHEN** the prompt is read
- **THEN** it asks that each input's source be named with the text the result gives, not paraphrased ("actual local weather" is not a source)

#### Scenario: Nothing to report yet
- **WHEN** the assessment cannot start because the user has not given the chemical's CAS number
- **THEN** the reply is the request alone, with no summary, results table or Limitations section

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

### Requirement: Every facility is covered
The prompt SHALL tell the agent to cover every facility of the chemical, not only the largest emitters, leaving a facility out only when a conservative screen shows it cannot reach a level of concern, and to report how many were screened out and against which thresholds, every facility assessed and every one kept at the worst case only (the person sees each one on the map); to narrow the scope only when the user asks for particular facilities or a place and to say so, and to request the inputs of several facilities together in one turn. The prompt SHALL NOT tell the agent to keep the scope manageable by choosing a subset itself.

#### Scenario: Prompt read
- **WHEN** the prompt is read
- **THEN** it says to cover every facility, screening rather than ranking them out, and names no tool

#### Scenario: User narrows the scope
- **WHEN** the user asks about one facility or one place
- **THEN** the prompt allows assessing only those and asks that the narrowing be stated

### Requirement: The reply does the work
The prompt SHALL tell the agent never to end a reply by announcing what it will do next, never to ask whether to proceed, and that a reply ends only when the assessment is written or something only the user can give is missing.

#### Scenario: Prompt read
- **WHEN** the prompt is read
- **THEN** it says to do the work rather than announce it and when a reply may end
