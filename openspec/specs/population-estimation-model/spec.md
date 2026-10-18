# population-estimation-model Specification

## Purpose

The pure arithmetic behind the population tool: scaling tract counts to a circle and converting age counts to age-band percentages.

## Requirements


### Requirement: Areal scaling
The system SHALL scale a residents count by the ratio of the circle's area to the tracts' land area, with the ratio never above 1; when the tracts' land area is zero the count SHALL be returned unscaled. Areas SHALL be in square meters.

#### Scenario: Half covered
- **WHEN** the circle's area is half the land area
- **THEN** the count is halved

#### Scenario: Circle larger than the land
- **WHEN** the circle's area exceeds the land area
- **THEN** the count is returned unchanged

#### Scenario: No land area
- **WHEN** the land area is zero
- **THEN** the count is returned unchanged

### Requirement: Age bands
The system SHALL turn counts of total residents, residents under 5, under 18 and 65 and over into percent of the total in the bands 0-4, 5-17 (under 18 minus under 5), 18-64 (the remainder) and 65 and over. The percentages SHALL sum to 100 within rounding and none SHALL be negative. A total that is not positive, a negative count, or counts that are not nested (under 5 above under 18, or under 18 plus 65 and over above the total) SHALL raise a `ValueError`; the counts SHALL NOT be clipped or adjusted.

#### Scenario: Typical counts
- **WHEN** the counts are 1,000, 100, 300 and 200
- **THEN** the bands are 10, 20, 50 and 20 percent

#### Scenario: Not nested
- **WHEN** under 5 exceeds under 18
- **THEN** a `ValueError` is raised

#### Scenario: No residents
- **WHEN** the total is zero
- **THEN** a `ValueError` is raised
