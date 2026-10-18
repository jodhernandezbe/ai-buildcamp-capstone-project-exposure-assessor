## ADDED Requirements

### Requirement: Exposure settings
The system SHALL read from an `[exposure]` table, and SHALL NOT embed in Python code: the list of (stability class, 10 m wind speed) combinations of the screening meteorology; the distance array (segments of start, end and step, in meters, and the minimum distance); the receptor height; the factor from the 1-hour to the annual average; the wind-profile exponent and the potential temperature gradient of each stability class; the exposure time, frequency and duration, and the cancer averaging time; and, for each age band, the inhalation rate and body weight; each with the source it comes from in a comment. The loader SHALL validate every entry on load.

#### Scenario: Settings loaded
- **WHEN** the loader is asked for the exposure settings
- **THEN** it returns the weather combinations, the expanded distance array, the factors and the per-band values from the file

#### Scenario: Changing the distance array
- **WHEN** a segment of the distance array is edited
- **THEN** subsequent calculations use it with no code change

#### Scenario: Invalid entry
- **WHEN** a stability class is not A to F, a wind speed or distance is not positive, a segment does not advance, the annual factor is outside 0 to 1, the frequency is above 365 days, the exposure time is above 24 hours, a band is missing or unknown, or an inhalation rate or body weight is not positive
- **THEN** the loader raises a `ValueError` naming the offending key
