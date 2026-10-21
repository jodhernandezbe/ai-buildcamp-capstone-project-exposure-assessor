# population-receptors-tool Specification

## Purpose

Tells the agent how many people live around a facility and how old they are, the receptor population of the screening exposure calculation.

## Requirements

### Requirement: Residents and age mix around a point
The system SHALL provide a tool that, given a latitude, longitude and an optional radius in kilometres, returns the estimated number of residents within that radius of the point and their age mix as percent of the total in the bands 0-4, 5-17, 18-64 and 65 and over (summing to 100), using the most recent configured Census ACS 5-year estimates of the census tracts that intersect the circle. The count SHALL be scaled by the ratio of the circle's area to the land area of those tracts, never above the tracts' full count. The result SHALL name its data source and vintage and carry a list of warnings. When no radius is given the configured default SHALL be used.

#### Scenario: Tracts partly inside the circle
- **WHEN** the circle covers half of the tracts' land area and the tracts hold 1,000 residents
- **THEN** about 500 residents are returned

#### Scenario: Circle larger than the tracts
- **WHEN** the circle's area exceeds the tracts' land area
- **THEN** the tracts' full count is returned, not more

#### Scenario: Age bands
- **WHEN** the tracts hold 1,000 residents of whom 100 are under 5, 300 are under 18 and 200 are 65 or over
- **THEN** the bands are 0-4 10, 5-17 20, 18-64 50 and 65+ 20 percent

#### Scenario: Several counties
- **WHEN** the intersecting tracts lie in more than one county
- **THEN** the estimates of every county are combined

#### Scenario: Default radius
- **WHEN** no radius is given
- **THEN** the configured default radius is used

#### Scenario: Tracts with no residents
- **WHEN** the intersecting tracts have usable estimates and all report zero residents
- **THEN** zero residents is returned with every age band at 0, labelled as census data, with a warning that the tracts report no residents (not the screening default)

### Requirement: Missing estimates are excluded, not repaired
The system SHALL treat an ACS estimate that is missing, not numeric, or negative (the ACS uses negative codes for estimates it could not compute) as not available, SHALL leave that tract out of the totals, and SHALL report in a warning how many intersecting tracts were left out. A response in which the age counts are inconsistent (for example under 5 above under 18, or under 18 and 65 and over together above the total) SHALL be treated as unusable.

#### Scenario: A tract with no estimate
- **WHEN** one of several intersecting tracts has a negative population code
- **THEN** the others are summed and the warnings say one tract was left out

#### Scenario: No tract has data
- **WHEN** every intersecting tract is unavailable
- **THEN** the screening default is returned with a warning saying no tract had usable estimates

#### Scenario: Inconsistent counts
- **WHEN** the under-5 count exceeds the under-18 count
- **THEN** the screening default is returned with a warning that the estimates were inconsistent

### Requirement: Census API key handling
The system SHALL send the Census API key with every Census Data API request, and SHALL NOT embed, log or return it. The key SHALL be the one made available to the current request when there is one (the web program supplies the key stored in the OS keychain for the duration of a turn), and otherwise the one in the environment variable named in the configuration. When neither is available it SHALL make no Census Data API request and SHALL return the screening default with a warning that names the variable. When the service rejects the key (it answers with a redirect to a missing-key page or an authorization error) the warning SHALL say the key was rejected.

#### Scenario: No key configured
- **WHEN** no request key is available and the variable is not set
- **THEN** no Census Data API request is made and the screening default is returned with a warning naming the variable

#### Scenario: Request key preferred
- **WHEN** a request key is available and the environment variable is also set
- **THEN** the Census Data API request carries the request key

#### Scenario: Key rejected
- **WHEN** the service redirects to its missing-key page
- **THEN** the screening default is returned with a warning that the key was missing or rejected, and the request is not retried

### Requirement: Validate the request
The system SHALL accept a latitude that is a finite number from -90 to 90, a longitude that is a finite number from -180 to 180 and a radius that is a finite number within the configured minimum and maximum (none a boolean). For an invalid value it SHALL make no request and SHALL return the screening default with a warning naming the invalid input.

#### Scenario: Radius too large
- **WHEN** the radius exceeds the configured maximum
- **THEN** no request is made and the warning names the radius and the maximum

#### Scenario: Radius not positive
- **WHEN** the radius is zero or negative
- **THEN** no request is made and the screening default is returned with a warning

### Requirement: Visible screening default
When the tract or ACS services cannot be used (a failed request after the configured retries, a non-success answer, malformed data, an unexpected shape, a truncated tract list, no intersecting tract, or any condition above that makes the data unusable), the system SHALL return the configured screening default (a residents-per-square-kilometre density applied to the circle's area, and an age mix), SHALL label its source as a screening default, and SHALL include a warning stating the reason. It SHALL NOT raise an error for data or network problems, and SHALL NOT present default values as census data.

#### Scenario: Open water or outside the United States
- **WHEN** no census tract intersects the circle
- **THEN** the screening default is returned with a warning that no census tract was found

#### Scenario: Tract list truncated
- **WHEN** the tract service reports that its transfer limit was exceeded
- **THEN** the screening default is returned with a warning that the tract list was incomplete

#### Scenario: Service unreachable
- **WHEN** every attempt times out
- **THEN** the screening default is returned with a warning that the Census data could not be read

### Requirement: Bounded, polite requests
The system SHALL make one tract request and one ACS request per county, wait the configured delay before each request, bound each by the configured timeout, retry throttling, server errors and timeouts the configured number of times, and SHALL NOT make more than the configured maximum number of county requests (a larger area gives the screening default with a warning).

#### Scenario: Too many counties
- **WHEN** the circle reaches more counties than the configured maximum
- **THEN** no ACS request is made and the screening default is returned with a warning

### Requirement: Tool description sets expectations
The tool's description, as seen by the LLM, SHALL state the units of each output, that the estimate is of residents (not workers or visitors) from ACS 5-year estimates with areal scaling that assumes an even spread within the tracts, that the coordinates should be the facility location from the emissions inventory, the radius limits, and that a screening default is labelled in `source` and `warnings`.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it names the inputs, the units of each output, the method's limits and the default behavior
