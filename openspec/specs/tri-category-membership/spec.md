## Purpose

Tells which TRI category, if any, contains a chemical. TRI reports many chemicals under a
category code (such as N420, lead compounds) instead of their own CAS number; this capability
reads the committed member list and answers membership questions without any network request.

## Requirements

### Requirement: Read the category member list
The system SHALL read the TRI category member list from the configured data file, with its
columns taken from configuration. Each row gives a member's CAS number, category code,
category name, member name and whether it is organic or inorganic. A category code written
as digits only (such as 1336363) is a CAS number written without hyphens and SHALL be
reported in hyphenated form (1336-36-3); every other code is kept as it is. A missing file or
a missing configured column SHALL raise an error naming it, because that is a setup error.

#### Scenario: Group code kept
- **WHEN** a row has category code "N420"
- **THEN** its category code is "N420"

#### Scenario: CAS-style code
- **WHEN** a row has category code "1336363"
- **THEN** its category code is "1336-36-3"

#### Scenario: File missing
- **WHEN** the configured file does not exist
- **THEN** an error naming the path is raised

### Requirement: Reject rows that cannot be trusted
The system SHALL drop a row whose member CAS number is not a valid CAS registry number
(including its check digit) or whose category code is empty, and SHALL report how many rows
were dropped and why. It SHALL NOT correct a CAS number, and SHALL NOT use the member name
to repair or identify a row.

#### Scenario: Bad check digit
- **WHEN** a row's CAS number fails its check digit
- **THEN** the row is not a member of any category and is counted as dropped

### Requirement: Membership lookup by CAS number
Given a CAS number, the system SHALL return every category that lists it: category code,
category name and chemical type. A CAS number listed under several categories SHALL return
all of them, in a stable order. A CAS number that no category lists SHALL return none. The
CAS number SHALL be validated first; an invalid one returns none and a warning. The lookup
SHALL make no network request, and the returned data SHALL be a copy that cannot change the
loaded list.

#### Scenario: Single category
- **WHEN** the CAS number 95-57-8 is looked up
- **THEN** the result is category N084, CHLOROPHENOLS

#### Scenario: Several categories
- **WHEN** a CAS number is listed under two categories
- **THEN** both are returned

#### Scenario: Not a member
- **WHEN** a CAS number appears in no row
- **THEN** no category is returned

#### Scenario: Invalid CAS number
- **WHEN** the input is "110-54-4"
- **THEN** no category is returned, a warning says the CAS number is invalid, and nothing else is read
