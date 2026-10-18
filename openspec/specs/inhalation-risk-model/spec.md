# inhalation-risk-model Specification

## Purpose

The pure arithmetic that turns an air concentration into an exposure concentration, a dose per age band, a hazard quotient and a cancer risk.

## Requirements


### Requirement: Exposure concentration
The system SHALL compute the inhalation exposure concentration as the air concentration times the exposure time per day over 24 hours times the exposure frequency over 365 days times the exposure duration over the averaging time in years, for a non-cancer averaging time equal to the exposure duration and a cancer averaging time of 70 years, and SHALL reject non-positive times, durations and frequencies outside 0 to 365 days per year or an exposure time outside 0 to 24 hours per day.

#### Scenario: Continuous exposure
- **WHEN** the exposure time is 24 hours, the frequency 365 days and the averaging time equals the duration
- **THEN** the exposure concentration equals the air concentration

#### Scenario: Cancer averaging
- **WHEN** the exposure duration is 26 years and the cancer averaging time is 70 years
- **THEN** the exposure concentration is the non-cancer one scaled by 26 over 70

#### Scenario: Impossible exposure
- **WHEN** the frequency is above 365 or the exposure time is above 24
- **THEN** a `ValueError` is raised

### Requirement: Dose per age band
The system SHALL compute the average daily dose of each age band from the exposure concentration, that band's inhalation rate and body weight, in milligrams per kilogram per day, and SHALL report the band with the highest dose. A band with zero share SHALL be omitted.

#### Scenario: Children dose higher
- **WHEN** a child band has a larger inhalation rate per kilogram than the adult band
- **THEN** its dose is larger for the same concentration

#### Scenario: Highest band
- **WHEN** several bands are present
- **THEN** the highest-dose band is named and its dose equals the maximum of the reported doses

### Requirement: Hazard quotient and cancer risk in consistent units
The system SHALL compare the non-cancer exposure concentration with the RfC (converted from mg/m^3 to ug/m^3) for the hazard quotient, and the cancer exposure concentration with the IUR (per ug/m^3) for the lifetime excess cancer risk, rejecting a non-positive RfC and a negative IUR.

#### Scenario: Hazard quotient
- **WHEN** the exposure concentration is 10 ug/m^3 and the RfC is 0.02 mg/m^3
- **THEN** the hazard quotient is 0.5

#### Scenario: Cancer risk
- **WHEN** the lifetime exposure concentration is 10 ug/m^3 and the IUR is 1e-6 per ug/m^3
- **THEN** the cancer risk is 1e-5

#### Scenario: Invalid benchmark
- **WHEN** the RfC is zero or the IUR is negative
- **THEN** a `ValueError` is raised
