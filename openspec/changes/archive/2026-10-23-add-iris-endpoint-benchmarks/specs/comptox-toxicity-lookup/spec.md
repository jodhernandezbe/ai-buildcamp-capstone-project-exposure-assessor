## ADDED Requirements

### Requirement: IRIS endpoint values take precedence for RfD and RfC
The system SHALL read the chemical's record from the configured CompTox IRIS endpoint and, where it holds a chronic RfD or RfC that can be read exactly, use it for `rfd` or `rfc` in preference to every ToxVal record. The value SHALL be reported with source `EPA IRIS: IRIS (CompTox IRIS endpoint)`, the exposure route of the field (oral for RfD, inhalation for RfC), the endpoint's critical-effect systems as its endpoint, a non-cancer assessment, and the record's last significant revision date. Subchronic values SHALL NOT be used. Slope factor and unit risk SHALL continue to come from ToxVal only.

#### Scenario: IRIS has a value ToxVal lacks
- **WHEN** the endpoint gives an RfC and ToxVal has no IRIS RfC for the chemical
- **THEN** the RfC is the endpoint's value with the IRIS source, ahead of any ToxVal source

#### Scenario: Endpoint has no value
- **WHEN** the endpoint's record has no chronic RfC (or no record exists)
- **THEN** the RfC comes from ToxVal as before

#### Scenario: Subchronic only
- **WHEN** the endpoint gives only a subchronic RfC
- **THEN** it is not used

#### Scenario: Cancer values
- **WHEN** the endpoint gives a tumor site
- **THEN** slope factor and unit risk still come from ToxVal

### Requirement: Read the endpoint's value text exactly
The system SHALL read a value only if its text is one number, optionally written as `a x 10 e` (for example `4 x 10 -3`), followed by one unit that converts to the field's target unit; the number SHALL be finite and greater than zero. Any other text (a range, an inequality, several values, no unit, an unknown unit) SHALL be refused: the endpoint then gives no value for that field and a warning says why, while ToxVal is used as before.

#### Scenario: Scientific notation
- **WHEN** the text is `2 x 10 -5 mg/m3`
- **THEN** the value is 0.00002 mg/m3

#### Scenario: Plain number
- **WHEN** the text is `5 mg/m3`
- **THEN** the value is 5 mg/m3

#### Scenario: Unreadable text
- **WHEN** the text is `1-2 mg/m3`, `> 1 mg/m3`, `5`, or two values on separate lines
- **THEN** no endpoint value is used for the field and a warning gives the text

### Requirement: Disagreement with ToxVal is reported
When the endpoint's value and a ToxVal IRIS record for the same field differ by more than the configured relative tolerance, the system SHALL use the endpoint's value and SHALL add a warning naming both values.

#### Scenario: Values agree
- **WHEN** the two values are within the tolerance
- **THEN** the endpoint's value is used and there is no warning

#### Scenario: Values differ
- **WHEN** the two values differ by more than the tolerance
- **THEN** the endpoint's value is used and a warning names both values

### Requirement: Endpoint failure does not lose ToxVal values
A failure of the IRIS endpoint request (after the configured retries) SHALL NOT be cached and SHALL NOT raise; the toxicity values SHALL then come from ToxVal alone.

#### Scenario: Endpoint unavailable
- **WHEN** the IRIS endpoint cannot be reached
- **THEN** RfD and RfC come from ToxVal and a later call asks the endpoint again
