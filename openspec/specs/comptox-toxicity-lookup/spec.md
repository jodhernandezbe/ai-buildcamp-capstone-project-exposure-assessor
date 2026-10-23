# comptox-toxicity-lookup Specification

## Purpose

Provides screening-level toxicity values (reference dose, reference concentration, slope factor, inhalation unit risk) for a chemical from EPA's CompTox ToxVal records, starting from a CAS registry number.

## Requirements

### Requirement: Extract configured toxicity values
The system SHALL return, for each toxicity value in the configured list, its numeric value, unit and source, taken from the CompTox ToxVal records of the chemical's DTXSID. Records match a toxicity value by exact record type label. Initially the list SHALL contain RfD ("RfD"), RfC ("RfC"), slope factor ("cancer slope factor") and inhalation unit risk ("cancer unit risk").

#### Scenario: Values present
- **WHEN** the ToxVal records include numeric entries for configured toxicity types
- **THEN** the result has one entry per configured toxicity value that was found, keyed by its configured key, each with value, unit and source

#### Scenario: Value absent
- **WHEN** no record matches a configured toxicity value, or the matching records have no numeric value
- **THEN** that value is omitted and the others are still returned

#### Scenario: Other record types ignored
- **WHEN** the records include types not in the configured list (e.g. NOAEL, LOAEL)
- **THEN** they do not appear in the result

#### Scenario: Alternate labels
- **WHEN** a configured toxicity value lists several accepted labels
- **THEN** a record carrying any of them is treated as that value

#### Scenario: Extending the list
- **WHEN** a new toxicity value is added to the configured list
- **THEN** it is extracted on the next lookup with no code change

### Requirement: Select among multiple records by source priority
The system SHALL choose, when several records match one toxicity value, first the highest-ranked source in the configured ordered source list (sources not in the list rank below all listed sources), and then, among that source's matching records, the most conservative value as configured for that toxicity value: the lowest for RfD and RfC, the highest for slope factor and unit risk. Remaining ties SHALL resolve to the first record returned by CompTox.

#### Scenario: Preferred source present
- **WHEN** records from a listed source and an unlisted source both match
- **THEN** the listed source's record is used and its source name is reported

#### Scenario: No listed source
- **WHEN** only unlisted sources match
- **THEN** the most conservative record among the first unlisted source's matches is used

#### Scenario: Range within one source
- **WHEN** one source gives two slope factors for the same chemical
- **THEN** the higher is returned

#### Scenario: Reference values within one source
- **WHEN** one source gives two RfC values
- **THEN** the lower is returned

### Requirement: Report toxicity units as provided
The system SHALL return the unit string supplied by CompTox with each value and SHALL NOT convert units.

#### Scenario: Unit passthrough
- **WHEN** a record's unit is "mg/kg-day"
- **THEN** the result carries exactly that unit string

### Requirement: Shared lookup behavior
The toxicity lookup SHALL use the same authentication, CAS-to-DTXSID resolution, failure handling and caching rules as the property lookup, and a chemical looked up for both properties and toxicity values SHALL be resolved to its DTXSID only once.

#### Scenario: Both lookups for one chemical
- **WHEN** properties and then toxicity values are requested for the same CAS number
- **THEN** the DTXSID search request is sent once

#### Scenario: Failure
- **WHEN** the ToxVal request fails, times out, or returns an error status or malformed body
- **THEN** no toxicity values are returned, nothing is raised, and a later call contacts CompTox again

#### Scenario: Missing API key
- **WHEN** the API-key environment variable is unset or blank
- **THEN** the system raises an error naming the variable, without contacting CompTox

### Requirement: Report the context of the chosen record
The system SHALL return, with each toxicity value, the exposure route recorded on the chosen record, the critical effect or cancer endpoint it records, and whether the record is a cancer or non-cancer assessment, taking them from the same record as the value. A field the source does not state (blank or "-") SHALL be reported as absent rather than guessed.

#### Scenario: Cancer endpoint
- **WHEN** the chosen slope-factor record names "leukemia" as its effect
- **THEN** the result carries that endpoint and a cancer assessment, and the route recorded on that record

#### Scenario: Unstated endpoint
- **WHEN** the chosen record gives no effect, or a non-text one
- **THEN** the endpoint is absent

#### Scenario: Context follows the value
- **WHEN** a source lists several values and the most conservative is chosen
- **THEN** the endpoint and route returned are those of that record

### Requirement: Filter by exposure route
The system SHALL accept a ToxVal record for a toxicity value only if the record's exposure route is one of the routes configured for that value, compared case-insensitively. Initially RfD and cancer slope factor SHALL accept oral, RfC and cancer unit risk SHALL accept inhalation, and RfD and RfC SHALL also accept "not specified".

#### Scenario: Wrong route
- **WHEN** a record labeled "cancer slope factor" has route inhalation
- **THEN** it is not used for the oral slope factor

#### Scenario: Route spelling
- **WHEN** a record's route is "Inhalation" and the configured route is "inhalation"
- **THEN** the record is accepted

#### Scenario: Route implied by the type
- **WHEN** an "RfC" record has route "not specified"
- **THEN** it is accepted, because RfC is an inhalation value by definition

### Requirement: Source names are those of the API, with IRIS first
The configured source order SHALL name sources exactly as the ToxVal API reports them in the `source` field (for IRIS, `EPA IRIS: IRIS`), and the shipped configuration SHALL rank EPA IRIS first.

#### Scenario: IRIS and another source both match
- **WHEN** a chemical has matching records from `EPA IRIS: IRIS` and from another source that appears earlier in the response
- **THEN** the IRIS record is used and its source is reported as `EPA IRIS: IRIS`

#### Scenario: Shipped order
- **WHEN** the shipped configuration is loaded
- **THEN** its first source is `EPA IRIS: IRIS`

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
