## MODIFIED Requirements

### Requirement: Primary NAICS code and title by control number
The system SHALL provide a tool that, given the TRI document control number of a submission (as returned in an emission record), returns the submission's primary NAICS code (primary indicator 1) and the title of that code, with a source label and warnings. The title SHALL come from the local Census code lists when the code is listed there, and otherwise from the Envirofacts NAICS reference table; it SHALL be reference text, not generated.

#### Scenario: Submission with a primary code
- **WHEN** the submission has one primary row and the code has a title in the local lists or the reference table
- **THEN** the code, its title and the source are returned with no warnings

#### Scenario: Listed code
- **WHEN** the submission's primary code is in the local code lists
- **THEN** the code, its local title and the source are returned and the reference table is not requested

#### Scenario: Unlisted code
- **WHEN** the submission's primary code is not in the local code lists and the reference table has it
- **THEN** the reference table's title is returned

#### Scenario: Title is words
- **WHEN** the code is 324110
- **THEN** the title returned is "Petroleum Refineries", not a number

### Requirement: Tool description says what to do with the result
The tool's description, as seen by the LLM, SHALL state that the title (not the code) is what the SCC process search needs, that the inventory already gives each record its title and the tool is called only when that title is null, that the result can be null (not guessed), what the warnings and the origin mean, that the industry does not by itself describe the emitting process, and that an unknown industry leads to the EPA global default stack.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it contains the title-not-code rule, the null-title condition, the null and origin meaning and the global default pointer
