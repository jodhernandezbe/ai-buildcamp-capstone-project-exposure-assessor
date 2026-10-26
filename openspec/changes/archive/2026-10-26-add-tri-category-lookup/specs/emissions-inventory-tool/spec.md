## MODIFIED Requirements

### Requirement: Facility emissions lookup by CAS
The system SHALL provide a tool that, given a CAS registry number or a TRI category code (such as N420), returns the facilities that reported releases of that chemical or category to the configured environmental media. The tool SHALL NOT take a reporting year. The identifier SHALL be validated before any request is made: a string that is neither a valid CAS number nor a category code present in the TRI category member list yields an empty result with a warning and no request. When the identifier is a category code, the result SHALL say that the releases were reported for the whole category, not for any one member, and SHALL NOT attribute them to a single member chemical.

The tool SHALL tell the model only the largest facilities. It SHALL return to the model the number of facilities found (`total_found`), the number matching the filters (`matching`), the number listed (`shown`), a `note` that says the list is partial when it is (null otherwise), and at most `[tri] max_listed` facilities ordered by emission rate, highest first. It SHALL also return the complete matching list, in the same order, as a tool artifact that the model never sees, for the program (the workspace). It MAY be given an optional `state` (postal abbreviation) and an optional `city` (exact name), both case-insensitive, which restrict `matching`, the listed facilities and the artifact to that place while `total_found` stays unfiltered.

#### Scenario: Known chemical
- **WHEN** the tool is called with a CAS number that TRI facilities have reported
- **THEN** the complete list has one record per (environmental medium, facility) for the configured media, and the model is told the largest of them

#### Scenario: Invalid CAS
- **WHEN** the tool is called with a string that is not a valid CAS number and not a known category code
- **THEN** it returns no facilities, logs a warning, and makes no HTTP request

#### Scenario: Category code
- **WHEN** the tool is called with "N420"
- **THEN** facilities that reported lead compounds are returned, and the result says the releases are for the lead-compounds category as a whole

#### Scenario: Unknown category code
- **WHEN** the tool is called with "N999", which no category lists
- **THEN** it returns no facilities, logs a warning, and makes no HTTP request

#### Scenario: Chemical never reported
- **WHEN** TRI has no rows for the CAS number
- **THEN** it returns no facilities

#### Scenario: Many facilities
- **WHEN** more facilities match than `[tri] max_listed`
- **THEN** the model is told the `max_listed` with the highest emission rates, highest first, and a note that the list is partial, while the artifact holds every matching facility

#### Scenario: Place filter
- **WHEN** the tool is called with `state` "tx" or with `city` "houston"
- **THEN** only facilities there are matched, listed and in the artifact, and `total_found` still counts every facility found

#### Scenario: Nothing matches the filter
- **WHEN** no facility matches the given `state` and `city`
- **THEN** `matching` and `shown` are 0 and the note says that no facility matches
