## ADDED Requirements

### Requirement: Asking the user for a missing value
The prompt SHALL explain, as assessment reasoning and without naming a tool or a call order,
when a value the analysis needs is missing and the missing value changes the result: the
assessor stops before concluding, asks the user once, in one message, for every such value,
says what each one is needed for, and offers the two answers the user may give (proceed without
it, or enter it with its unit). The prompt SHALL NOT tell the assessor to guess, estimate or
borrow a value that is missing from the evidence as a substitute for asking, except where the
read-across rule already allows a labelled estimate.

#### Scenario: Missing value that changes the result
- **WHEN** the prompt is read
- **THEN** it says to ask the user once, in one message, for every missing value that changes the result, and to name what each is needed for

#### Scenario: Missing value that does not change the result
- **WHEN** the prompt is read
- **THEN** it says a missing value that the requested result does not use is not raised with the user

#### Scenario: User's answers
- **WHEN** the prompt is read
- **THEN** it says a value the user entered is used as the user's own figure and is reported as user-provided, and a value the user declined is reported as absent, not estimated

### Requirement: Missing-value rule does not reopen the CAS rule
The missing-value request SHALL NOT ask for, or accept, a CAS registry number that the user did
not give; the CAS rule of the prompt stands unchanged.

#### Scenario: Missing CAS number is not a property
- **WHEN** the chemical's CAS number is missing
- **THEN** the reply asks for the CAS number as before and does not open a missing-value request for it
