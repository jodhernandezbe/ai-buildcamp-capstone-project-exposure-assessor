## Purpose

Tells the agent what industry a facility is in, in words, so that process-typical stack parameters can be found when the facility has no stack of its own in the NEI.

## ADDED Requirements

### Requirement: Primary NAICS code and title by control number
The system SHALL provide a tool that, given the TRI document control number of a submission (as returned in an emission record), returns the submission's primary NAICS code (primary indicator 1) and the title of that code, both taken from Envirofacts, with a source label and warnings. The title SHALL be the text of the NAICS reference table, not generated.

#### Scenario: Submission with a primary code
- **WHEN** the submission has one primary row and the reference table has the code's title
- **THEN** the code, its title and the source are returned with no warnings

#### Scenario: Title is words
- **WHEN** the code is 324110
- **THEN** the title returned is "Petroleum Refineries", not a number

### Requirement: Origin of the code
The result SHALL state whether the facility reported the code (`reported`) or EPA assigned it (`assigned`), or null when TRI does not say. For an assigned code the warnings SHALL say that EPA assigned it and that it may be generic.

#### Scenario: Assigned code
- **WHEN** the primary row's source is "ASSIGNED"
- **THEN** `code_origin` is "assigned" and a warning says EPA assigned it

#### Scenario: Reported code
- **WHEN** the primary row's source is "Reported"
- **THEN** `code_origin` is "reported" and there is no assignment warning

### Requirement: Deterministic choice among primary rows
When more than one primary row is returned, the system SHALL choose the one with the lowest sequence number, then the smaller code, and SHALL warn that several primary codes were listed.

#### Scenario: Two primary rows
- **WHEN** two rows are primary with sequence numbers 1 and 2
- **THEN** the sequence 1 code is returned and a warning says two were listed

### Requirement: Fail closed
The system SHALL return null code and title with a warning, and SHALL NOT raise, when the control number is invalid (blank or not digits; no request is made), when the submission has no primary NAICS row, when the only primary code is a configured placeholder (such as 999999, "AFS Migration"), or when the request fails after its retries. When the code is found but its title is not, the code SHALL be returned with a null title and a warning that the title is needed before the SCC search can be used.

#### Scenario: Invalid control number
- **WHEN** the control number is "abc"
- **THEN** no request is made and the result is null with a warning

#### Scenario: Placeholder code
- **WHEN** the only primary code is 999999
- **THEN** the result is null with a warning that the code is a placeholder, not an industry

#### Scenario: Title not found
- **WHEN** the reference table has no row for the code
- **THEN** the code is returned, the title is null and the warning says the title is missing

#### Scenario: Service unreachable
- **WHEN** every attempt fails
- **THEN** the result is null with a warning, and no error is raised

### Requirement: Tool description says what to do with the result
The tool's description, as seen by the LLM, SHALL state that the title (not the code) is what the SCC process search needs, that it is called only for facilities being assessed, that the result can be null (not guessed), what the warnings and the origin mean, that the industry does not by itself describe the emitting process, and that an unknown industry leads to the EPA global default stack.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it contains the title-not-code rule, the null and origin meaning and the global default pointer
