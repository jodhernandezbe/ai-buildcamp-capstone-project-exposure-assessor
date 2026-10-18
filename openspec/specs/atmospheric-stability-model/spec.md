# atmospheric-stability-model Specification

## Purpose

The pure atmospheric rules behind the meteorology tool: Pasquill-Gifford stability classification of an hour of weather and the summary of an hourly series into representative conditions.

## Requirements


### Requirement: Pasquill-Gifford class of an hour
The system SHALL classify an hour from its wind speed at 10 m (m/s), total solar radiation (W/m^2), total cloud cover and low cloud cover (percent) and whether it is daytime, using EPA's keys (Meteorological Monitoring Guidance for Regulatory Modeling Applications, EPA-454/R-99-005): an hour whose low cloud cover is 100 percent (overcast with a low ceiling) SHALL be class D, day or night; a daytime hour SHALL use the solar radiation/delta-T (SRDT) daytime key (Table 6-7: radiation of at least 925, 675 to 925, 175 to 675, and below 175 W/m^2 against wind speed below 2, 2 to 3, 3 to 5, 5 to 6, and 6 m/s or more); a night hour SHALL use Turner's key (Tables 6-4 and 6-6) with net radiation index -1 when total cloud cover exceeds 40 percent and -2 otherwise, stability classes 6 and 7 (F and G) combined as F. The classification SHALL be a fixed table, independent of location and date.

#### Scenario: Strong sun, light wind
- **WHEN** it is daytime, radiation is at least 925 W/m^2 and wind speed is below 3 m/s
- **THEN** the class is A

#### Scenario: Moderate sun, light wind
- **WHEN** it is daytime, radiation is between 675 and 925 W/m^2 and wind speed is between 2 and 3 m/s
- **THEN** the class is B

#### Scenario: Weak sun
- **WHEN** it is daytime and radiation is below 175 W/m^2
- **THEN** the class is D at any wind speed

#### Scenario: Clear night, light wind
- **WHEN** it is night, total cloud cover is 40 percent or less and wind speed is below 3.4 m/s
- **THEN** the class is F

#### Scenario: Cloudy night
- **WHEN** it is night and total cloud cover is above 40 percent
- **THEN** the class is F below 1.9 m/s, E from 1.9 to below 3.4 m/s, and D from 3.4 m/s

#### Scenario: Clear night, stronger wind
- **WHEN** it is night, total cloud cover is 40 percent or less and wind speed is 3.4 to below 5.5 m/s
- **THEN** the class is E, and from 5.5 m/s it is D

#### Scenario: Low overcast
- **WHEN** low cloud cover is 100 percent
- **THEN** the class is D, day or night

### Requirement: Reject impossible hours
The classification SHALL raise a `ValueError` for a wind speed or radiation that is negative or not finite and for a total or low cloud cover that is not finite or is outside 0 to 100 percent. It SHALL NOT clip or guess them.

#### Scenario: Negative wind speed
- **WHEN** the wind speed is -1 m/s
- **THEN** a `ValueError` is raised

#### Scenario: Cloud cover above 100
- **WHEN** the cloud cover is 120 percent
- **THEN** a `ValueError` is raised

### Requirement: Summary of an hourly series
The system SHALL reduce equal-length hourly series of wind speed, direction, class and temperature to: the mean wind speed, not below a given minimum; the centre of the most frequent direction sector of a given width, counted on the circle; the most frequent class; and the mean temperature. Ties SHALL be broken deterministically (the smallest sector centre; the class earliest in the alphabet). An empty series or one with lengths that differ SHALL raise a `ValueError`.

#### Scenario: Mean wind with a minimum
- **WHEN** the hourly speeds average 0.4 m/s and the minimum is 1 m/s
- **THEN** the summary speed is 1 m/s

#### Scenario: Sector on the circle
- **WHEN** hours are at 358, 2, 4 and 90 degrees with 10 degree sectors
- **THEN** the prevailing direction is 0 degrees

#### Scenario: Tied classes
- **WHEN** two classes are equally frequent
- **THEN** the one earlier in the alphabet is returned

#### Scenario: Empty or mismatched input
- **WHEN** the series are empty or have different lengths
- **THEN** a `ValueError` is raised
