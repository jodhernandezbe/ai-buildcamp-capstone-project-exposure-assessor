# comptox-property-lookup Specification

## Purpose

Provides screening-level physical-chemical property values (initially vapor pressure and density) for a chemical from EPA's CompTox Chemicals Dashboard, starting from a CAS registry number.

## Requirements

### Requirement: Extract configured properties
The system SHALL return, for each property named in the configured property list, its value, unit and source, taken from the CompTox property summary for the DTXSID. Initially the list SHALL contain vapor pressure and density.

#### Scenario: Properties present
- **WHEN** the summary contains entries for all configured properties
- **THEN** the result has one entry per configured property, keyed by the configured key, each with value, unit and source

#### Scenario: Property absent from summary
- **WHEN** a configured property has no entry, or has no experimental or predicted value
- **THEN** that property is omitted from the result and the others are still returned

#### Scenario: Unconfigured properties ignored
- **WHEN** the summary contains properties not in the configured list
- **THEN** they do not appear in the result

#### Scenario: Extending the list
- **WHEN** a new property is added to the configured list
- **THEN** it is extracted on the next lookup with no code change

### Requirement: Prefer experimental over predicted
The system SHALL use the experimental median when it is available, and otherwise the predicted median, and SHALL report which was used.

#### Scenario: Experimental available
- **WHEN** both experimental and predicted medians exist
- **THEN** the value is the experimental median and the source is "experimental"

#### Scenario: Only predicted available
- **WHEN** the experimental median is null and the predicted median exists
- **THEN** the value is the predicted median and the source is "predicted"

### Requirement: Report units as provided
The system SHALL return the unit string supplied by CompTox with each value and SHALL NOT convert units.

#### Scenario: Unit passthrough
- **WHEN** CompTox reports vapor pressure in "mmHg" and density in "g/cm^3"
- **THEN** the result carries those exact unit strings

### Requirement: Authenticated requests
The system SHALL send the CompTox API key with every request, and SHALL NOT store the key in code or configuration files. The key SHALL be the one made available to the current request when there is one (the web program supplies the key stored in the OS keychain for the duration of a turn), and otherwise the one read from the configured environment variable. The key SHALL be resolved afresh for every request and not held by the client between requests.

#### Scenario: Key available
- **WHEN** the configured environment variable is set and no request key is available
- **THEN** its value is sent in the configured API-key header

#### Scenario: Request key preferred
- **WHEN** a request key is available and the environment variable is also set
- **THEN** the request key is sent in the configured API-key header

#### Scenario: Key missing
- **WHEN** no request key is available and the configured environment variable is unset or blank
- **THEN** the system raises an error naming the variable, without contacting CompTox

#### Scenario: Key not retained
- **WHEN** a request has been made under one request key and a later one under another
- **THEN** each request sends its own key

### Requirement: Resilient to service failures
The system SHALL return no properties, rather than raise, when CompTox is unreachable, times out, or answers with an error status or malformed body. A definitive "no match" answer (an empty result, HTTP 404, or HTTP 400 stating that zero results were found) MAY be cached; transient failures SHALL NOT be cached.

#### Scenario: Network failure
- **WHEN** a request fails or times out
- **THEN** no properties are returned and a later call for the same input contacts CompTox again

#### Scenario: Repeat lookup
- **WHEN** the same CAS number is looked up again after a successful lookup
- **THEN** the cached result is returned without contacting CompTox

#### Scenario: Zero-results answer
- **WHEN** CompTox answers HTTP 400 stating that zero results were found for the CAS number
- **THEN** it is treated as "no match", not as a transient failure

### Requirement: Resolve CAS number to DTXSID
The system SHALL resolve a CAS registry number to a DSSTox substance identifier (DTXSID) by querying CompTox's exact CAS search, and SHALL accept a result only if CompTox reports it as a CAS-number match whose CAS equals the requested one. The accepted match's preferred name SHALL be kept with the DTXSID when it is a non-empty string, and left absent otherwise (a missing name never rejects the match). The CAS number SHALL be validated (format and check digit) and normalized to its hyphenated form before any request.

#### Scenario: Known CAS number
- **WHEN** CompTox returns a CAS-number match whose CAS equals the requested CAS
- **THEN** the system uses the DTXSID of that match for the property request and keeps its preferred name

#### Scenario: Name absent or not text
- **WHEN** the accepted match has no preferred name, or it is blank or not a string
- **THEN** the DTXSID is still used and the name is absent

#### Scenario: Hyphens omitted
- **WHEN** the CAS number is given without hyphens, e.g. "71432"
- **THEN** it is looked up as "71-43-2"

#### Scenario: Match of another kind
- **WHEN** CompTox returns a result that is not a CAS-number match, or whose CAS differs from the one requested
- **THEN** the result is ignored and the system returns no properties

#### Scenario: Invalid CAS number
- **WHEN** the input is not a valid CAS number (wrong format or check digit)
- **THEN** the system returns no properties without contacting CompTox

#### Scenario: No match
- **WHEN** CompTox reports that no chemical matches the CAS number
- **THEN** the system returns no properties and does not raise

#### Scenario: Blank input
- **WHEN** the CAS number is empty or whitespace
- **THEN** the system returns no properties without contacting CompTox

### Requirement: Provide the chemical's molecular weight
The system SHALL return the molecular weight that CompTox's chemical detail holds for the DTXSID of a verified CAS match, reading the configured response field and reporting it in the configured unit, and SHALL return no value when CompTox gives none or gives something that is not a finite number.

#### Scenario: Molecular weight present
- **WHEN** the chemical detail carries a value in the configured field
- **THEN** that number is returned for the CAS number

#### Scenario: Not available
- **WHEN** the detail has no value in the configured field, a non-numeric one, or a non-finite one
- **THEN** no value is returned and nothing is raised

#### Scenario: One CAS search
- **WHEN** molecular weight, properties and toxicity values are all requested for one CAS number
- **THEN** the CAS search is sent once

### Requirement: Treat service responses as untrusted
The system SHALL check the type and shape of every CompTox field it uses before using it, and SHALL ignore any value that is missing, of the wrong type, not a finite number, or from a record that does not belong to the requested chemical, rather than guess or coerce it.

#### Scenario: Unexpected shape
- **WHEN** a response is not a list, an entry is not an object, or a used field has the wrong type
- **THEN** that data is ignored and no partial or coerced value is returned

#### Scenario: Non-finite number
- **WHEN** a numeric field is NaN or infinite
- **THEN** it is treated as absent

#### Scenario: Record for another chemical
- **WHEN** a ToxVal record's DTXSID differs from the one requested
- **THEN** the record is ignored

### Requirement: Certificate verification waives the dates only, by setting
The CompTox client SHALL verify the service's TLS certificate fully by default. When the `accept_expired_certificate` setting is on, it SHALL skip only the certificate's validity-dates check: the chain SHALL still be validated against the trusted roots and the host name SHALL still be checked. Verification SHALL never be turned off, and the API key SHALL never be sent over an unverified connection.

#### Scenario: Default
- **WHEN** the setting is off
- **THEN** the client verifies the certificate fully

#### Scenario: Lapsed certificate accepted
- **WHEN** the setting is on and the service's certificate has expired but is otherwise valid for the host
- **THEN** the request succeeds

#### Scenario: Wrong host or untrusted chain
- **WHEN** the setting is on and the certificate is for another host or not signed by a trusted root
- **THEN** the request fails
