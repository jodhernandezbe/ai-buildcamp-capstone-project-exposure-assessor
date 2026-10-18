# meteorological-conditions-tool Specification

## Purpose

Gives the agent the representative wind, atmospheric stability and ambient temperature at a facility's location, the meteorological inputs of the screening dispersion calculation.

## Requirements


### Requirement: Representative conditions at a point
The system SHALL provide a tool that, given a latitude, longitude and an optional reporting year, returns for that point: wind speed (m/s), prevailing wind direction (degrees clockwise from north, the direction the wind blows from), Pasquill-Gifford stability class (A to F) and ambient temperature (K), summarizing one year of hourly historical data from the configured meteorological archive. The wind speed SHALL be the annual mean but not below the configured minimum. The wind direction SHALL be the centre of the most frequent sector of the configured width. The stability class SHALL be the most frequent hourly class. The ambient temperature SHALL be the annual mean. The result SHALL name its data source and year, and carry a list of warnings.

#### Scenario: Full year of valid data
- **WHEN** the archive returns hourly data for the whole year
- **THEN** the tool returns the four values, a source naming the archive and the year, and no warnings

#### Scenario: Calm year
- **WHEN** the annual mean wind speed is below the configured minimum
- **THEN** the minimum is returned as the wind speed

#### Scenario: Wind from the north
- **WHEN** the most frequent directions straddle 0 degrees (for example 355 and 5 degrees)
- **THEN** the prevailing direction is reported on the circle, within 0 to 360

#### Scenario: Default year
- **WHEN** no reporting year is given
- **THEN** the configured default year is used

### Requirement: Invalid hours are excluded, not repaired
The system SHALL exclude an hour from the summary when its wind speed, wind direction, solar radiation, total or low cloud cover or day/night flag is missing, not a finite number, or outside its physical range (negative wind speed or radiation, cloud cover outside 0 to 100 percent, direction outside 0 to 360 degrees, a day/night flag other than 0 or 1). A missing temperature SHALL exclude the hour from the temperature mean only. The warnings SHALL state how many hours were excluded. A response whose hourly series differ in length SHALL be treated as unusable.

#### Scenario: Some hours missing
- **WHEN** a few hours lack a wind speed
- **THEN** they are left out of every summary value and the warnings give their number

#### Scenario: No temperature at all
- **WHEN** every hour lacks a temperature but the other values are valid
- **THEN** the wind and stability values are returned with the screening default temperature and a warning saying so

#### Scenario: No usable hour
- **WHEN** every hour is excluded
- **THEN** the screening default is returned with a warning saying no usable hourly data were found

#### Scenario: Mismatched series
- **WHEN** the hourly lists have different lengths
- **THEN** the screening default is returned with a warning that the response was unusable

### Requirement: Validate the request
The system SHALL accept a latitude that is a finite number from -90 to 90, a longitude that is a finite number from -180 to 180 (neither a boolean), and a reporting year that is an integer within the configured available range. For an invalid value it SHALL make no request and SHALL return the screening default with a warning naming the invalid input.

#### Scenario: Latitude out of range
- **WHEN** the latitude is 95
- **THEN** no request is made and the screening default is returned with a warning naming the latitude

#### Scenario: Year outside the archive
- **WHEN** the reporting year is before the first available year or after the last complete one
- **THEN** no request is made and the screening default is returned with a warning naming the year

### Requirement: Visible screening default
When the archive cannot be read (a failed request after the configured retries, a non-success response, malformed data, an unexpected shape or no usable hour), the system SHALL return the configured screening default (wind speed, direction, stability class and temperature), SHALL label its source as a screening default, and SHALL include a warning stating the reason. It SHALL NOT raise an error for data or network problems, and SHALL NOT present default values as measured data.

#### Scenario: Archive unreachable
- **WHEN** every attempt times out
- **THEN** the screening default is returned, labelled as such, with a warning saying the archive could not be reached

#### Scenario: Archive rejects the request
- **WHEN** the archive answers with a client error
- **THEN** the screening default is returned with a warning naming the status, and the request is not retried

### Requirement: Bounded, polite requests
The system SHALL make one request per call, wait the configured delay before it, bound it by the configured timeout, and retry throttling (HTTP 429), server errors and timeouts the configured number of times with increasing waits, honouring a `Retry-After` header up to the timeout.

#### Scenario: Throttled then succeeds
- **WHEN** the first attempt returns HTTP 429 and the second succeeds
- **THEN** the second attempt's data are used

### Requirement: Tool description sets expectations
The tool's description, as seen by the LLM, SHALL state the units of each output, that the values are annual representatives for the year (not worst-case conditions) taken from a coarse gridded reanalysis rather than a nearby station, that the coordinates should be the facility location from the emissions inventory, and that a screening default is labelled in `source` and `warnings`.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, the year semantics, the data resolution and the default behavior
