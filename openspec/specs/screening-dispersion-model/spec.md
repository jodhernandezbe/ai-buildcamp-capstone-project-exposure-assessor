# screening-dispersion-model Specification

## Purpose

The pure atmospheric equations behind the exposure tool: how high the plume rises, how the wind changes with height, and the search for the worst-case concentration over weather and distance as EPA's SCREEN3 does.

## Requirements


### Requirement: Buoyant plume rise
The system SHALL compute the buoyancy flux of a stack as g times exit velocity times diameter squared times the excess of stack gas over ambient temperature, divided by four times the stack gas temperature, and from it the final plume rise by Briggs' formulas for unstable and neutral conditions (two flux regimes) and for stable conditions (which use the ambient temperature and the configured potential temperature gradient of the class), plus Briggs' stack-tip downwash correction to the stack height when the exit velocity is below 1.5 times the wind speed at the stack. A stack gas not hotter than the ambient air SHALL give no buoyant rise. All lengths SHALL be in meters, speeds in m/s and temperatures in kelvin.

#### Scenario: Hotter gas rises more
- **WHEN** only the stack gas temperature is raised above ambient
- **THEN** the buoyancy flux and the plume rise increase

#### Scenario: Gas at ambient temperature
- **WHEN** the stack gas temperature equals the ambient temperature
- **THEN** the buoyancy flux is zero and there is no buoyant rise

#### Scenario: Stronger wind lowers the rise
- **WHEN** the wind speed at the stack is raised
- **THEN** the final plume rise does not increase

#### Scenario: Stack-tip downwash
- **WHEN** the exit velocity is below 1.5 times the wind speed at the stack
- **THEN** the effective stack height is reduced by the downwash correction, and is not reduced otherwise

#### Scenario: Impossible input
- **WHEN** a diameter or velocity is not positive, or a temperature is not positive
- **THEN** a `ValueError` is raised

### Requirement: Wind speed at stack height
The system SHALL adjust a 10 m wind speed to the release height with the power law using an exponent per stability class, and SHALL NOT adjust it for release heights below 10 m.

#### Scenario: Taller release
- **WHEN** the release height is above 10 m
- **THEN** the wind speed at the release height is larger than the 10 m wind speed, and more so for stable classes

#### Scenario: Low release
- **WHEN** the release height is below 10 m
- **THEN** the 10 m wind speed is used unchanged

#### Scenario: Unknown class
- **WHEN** the stability class is not A to F
- **THEN** a `ValueError` is raised

### Requirement: Worst case over weather and distance
The system SHALL find the maximum ground-level centerline concentration of a source over a given set of (stability class, 10 m wind speed) combinations and a given set of distances, using the Gaussian plume with ground reflection and the Briggs rural dispersion coefficients at the effective release height, and SHALL return the maximum with the combination, the distance and the effective release height that gave it. The set of combinations and the distances SHALL be inputs, not constants of the model.

#### Scenario: Maximum is attained
- **WHEN** the search is run
- **THEN** the returned concentration equals the plume concentration at the returned combination and distance, and no other evaluated pair gives more

#### Scenario: Linear in emission rate
- **WHEN** the emission rate is doubled
- **THEN** the maximum is doubled and the combination and distance are unchanged

#### Scenario: Distances below the minimum are ignored
- **WHEN** a minimum distance is given
- **THEN** only distances at or beyond it are evaluated

#### Scenario: Empty set
- **WHEN** the combinations or distances are empty
- **THEN** a `ValueError` is raised

#### Scenario: Distance outside the dispersion model's validity
- **WHEN** a distance is below 100 m or above 10 km, the range in which the dispersion coefficients are valid
- **THEN** a `ValueError` is raised and nothing is extrapolated

### Requirement: Short-term to annual conversion
The system SHALL convert a 1-hour concentration to an annual-average concentration by a given factor between 0 and 1 and SHALL reject a factor outside that range.

#### Scenario: Factor applied
- **WHEN** the factor is 0.08 and the 1-hour value is 100
- **THEN** the annual value is 8

#### Scenario: Factor out of range
- **WHEN** the factor is above 1 or not positive
- **THEN** a `ValueError` is raised

### Requirement: Concentration at a stated distance for a fixed scenario
The model SHALL give the 1-hour ground-level centerline concentration (ug/m^3) at a stated downwind distance (m) for a scenario's emission rate, stability class, wind speed and stack, using the same dispersion and plume rise as the worst-case search; the annual average follows by the same factor as for the maximum. At the distance of the worst-case maximum it SHALL equal that maximum, and it SHALL NOT exceed it at any other distance.

#### Scenario: At the maximum
- **WHEN** the distance is the one of the worst-case maximum
- **THEN** the concentration equals the maximum

#### Scenario: Elsewhere
- **WHEN** the distance is smaller or larger than the one of the maximum
- **THEN** the concentration is not larger than the maximum

#### Scenario: Invalid input
- **WHEN** the distance is not finite or outside 100 to 10,000 m
- **THEN** the model raises rather than returning a number
