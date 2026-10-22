## ADDED Requirements

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
