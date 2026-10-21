## Purpose

Keeps the copilot on its scientific mission: off-topic requests get a warm, in-character
redirect without running any tools, while domain questions and natural follow-ups pass through.

## ADDED Requirements

### Requirement: Opt-in scope check before the agent
The agent graph SHALL accept an optional scope check. When it is enabled, every user turn SHALL
first be classified, using the injected chat model with a prompt loaded from the prompt files,
as in or out of scope from the latest user message plus a short window of the preceding
conversation (so follow-ups such as "what does that mean?" are judged in context). When it is
not enabled, the graph SHALL behave exactly as before.

#### Scenario: Disabled by default
- **WHEN** the agent is built without a scope check
- **THEN** the graph's nodes, edges and model calls are unchanged from the current agent

#### Scenario: Context-aware follow-up
- **WHEN** after an assessment the user asks "why is the HQ so low?"
- **THEN** the turn is classified in scope

### Requirement: In-scope turns pass through
Turns about chemical exposure and risk assessment, TRI / NEI / ECHO / FRS facility data,
dispersion and plume physics, stack parameters and their fallbacks, toxicity benchmarks and
hazard quotients, read-across surrogates, receptor demographics, environmental regulation, and
conversational turns (greetings, thanks, clarifications, methodology questions, unit
conversions, scenario comparisons, interpreting the map or results) SHALL proceed to the
tool-bound agent unchanged.

#### Scenario: Domain query
- **WHEN** the user asks to map hexane releases near Houston
- **THEN** the turn reaches the agent and tools may run

#### Scenario: Greeting
- **WHEN** the user says "hi, what can you do?"
- **THEN** the turn reaches the agent

#### Scenario: Methodology question
- **WHEN** the user asks how Briggs plume rise works
- **THEN** the turn reaches the agent

### Requirement: Off-topic turns are redirected without tools
Turns outside the domain (general programming, creative writing, sports, finance, recipes,
political debate and similar) SHALL be answered with a short, warm assistant message that
declines the request in character and offers relevant things the copilot can do. The reply
SHALL come from the same classifier call. The tool-bound model SHALL NOT be called and no tool
SHALL run. The reply SHALL be an ordinary assistant message, not an error.

#### Scenario: Coding request
- **WHEN** the user asks for a React snake game
- **THEN** the assistant replies with a polite redirect, the agent model is not invoked and no tool runs

#### Scenario: Redirect is part of history
- **WHEN** a redirect is followed by an in-scope question
- **THEN** the agent sees both earlier messages and answers the new question normally

### Requirement: Classifier failure does not block the user
If the classifier call fails or returns an unusable verdict, the turn SHALL be treated as in
scope and passed to the agent, and a warning SHALL be logged (redacted). This is a deliberate
fail-open: the agent remains bound to its tools and system prompt, so a classifier error costs
at most one unneeded agent run, whereas failing closed would refuse legitimate assessments.

#### Scenario: Malformed verdict
- **WHEN** the classifier returns output that does not match the verdict shape
- **THEN** the turn reaches the agent and a warning is logged

#### Scenario: Out of scope without reply text
- **WHEN** the verdict says out of scope but has a blank reply
- **THEN** the configured fallback redirect text from the prompt files is used

### Requirement: Scope addendum for the web program
The web program SHALL run the agent with the standard system prompt followed by a scope
addendum loaded from the prompt files, which tells the assessor its scope and how to decline
in character. The standard system prompt used by the command-line program and the evaluations
SHALL remain unchanged.

#### Scenario: Web prompt
- **WHEN** the web program builds the agent
- **THEN** its system prompt is the standard prompt followed by the addendum

#### Scenario: CLI prompt untouched
- **WHEN** the command-line program builds the agent
- **THEN** its system prompt is byte-identical to the standard prompt
