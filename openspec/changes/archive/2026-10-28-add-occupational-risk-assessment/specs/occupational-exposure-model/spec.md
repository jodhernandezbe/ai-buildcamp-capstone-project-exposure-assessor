## Purpose

The pure arithmetic of the worker screening: a mass-balance workplace air concentration, its 8-hour time-weighted average and ratio to an occupational exposure limit, and a chronic worker dose, hazard quotient and cancer risk, with a risk tier. Screening level only.

## ADDED Requirements

### Requirement: Workplace box-model concentration
The system SHALL compute the generation rate in mg/s as the annual fugitive release in kg/yr times 10^6 over the operating days per year times the operating hours per day times 3,600, and the workplace concentration in mg/m^3 as the generation rate over the ventilation rate in m^3/s times the mixing factor. It SHALL reject a non-finite or negative release, and non-positive operating days, hours, ventilation rate or mixing factor, and a mixing factor above 1, with a `ValueError`.

#### Scenario: Worked example
- **WHEN** the release is 1,000 kg/yr, the plant runs 250 days/yr and 16 h/day, the ventilation is 1.416 m^3/s and the mixing factor 0.5
- **THEN** the generation rate is 1,000 x 10^6 over 250 x 16 x 3,600 mg/s and the concentration is that rate over 0.708 m^3/s

#### Scenario: Doubled release
- **WHEN** the release is doubled and nothing else changes
- **THEN** the concentration is doubled

#### Scenario: Smaller ventilation
- **WHEN** only the ventilation rate or the mixing factor is lowered
- **THEN** the concentration is higher

#### Scenario: Invalid input
- **WHEN** the hours per day are zero, the mixing factor is 1.5 or the release is NaN
- **THEN** a `ValueError` is raised

### Requirement: Two ventilation tiers
The system SHALL evaluate the box model for a baseline tier and a worst-case (enclosed zone) tier whose ventilation rates and mixing factors come from configuration (baseline 3,000 ft^3/min and 0.5; worst case 500 ft^3/min and 0.1), converting ft^3/min to m^3/s with the shared unit conversion, and SHALL return both with the tier values used.

#### Scenario: Worst case is higher
- **WHEN** both tiers are evaluated for one release and schedule
- **THEN** the worst-case concentration is greater than the baseline one

#### Scenario: Configured tiers
- **WHEN** a tier's ventilation rate is changed in the configuration
- **THEN** its concentration changes with no code change

### Requirement: Eight-hour TWA and limit ratio
The system SHALL compute the 8-hour time-weighted average in mg/m^3 as the workplace concentration times the smaller of the hours per day and 8, over 8, and the limit ratio as that average over the occupational exposure limit in mg/m^3, rejecting a non-positive limit.

#### Scenario: Long shift is capped
- **WHEN** the plant runs 16 h/day
- **THEN** the TWA equals the workplace concentration

#### Scenario: Short shift is diluted
- **WHEN** the plant runs 4 h/day
- **THEN** the TWA is half the workplace concentration

#### Scenario: Ratio
- **WHEN** the TWA is 0.5 mg/m^3 and the limit 5 mg/m^3
- **THEN** the ratio is 0.1

#### Scenario: Non-positive limit
- **WHEN** the limit is zero
- **THEN** a `ValueError` is raised

### Requirement: Chronic worker dose, hazard quotient and cancer risk
The system SHALL compute the worker average daily concentration as the TWA times the ratio of the shift inhalation volume to the 24-hour volume (10 over 20 m^3/day, configured) times the worker's days per year (the smaller of 250 and the plant's operating days) over 365, and the lifetime average concentration as the same product with the tenure (40 years, configured) over the 78-year lifetime instead of over one year of days. The hazard quotient SHALL be the average daily concentration over the RfC in mg/m^3 and the cancer risk the lifetime average concentration times 1,000 (to ug/m^3) times the IUR per ug/m^3. A missing RfC or IUR SHALL give a null hazard quotient or cancer risk, never zero; a non-positive RfC or negative IUR SHALL be rejected.

#### Scenario: Year-round shift
- **WHEN** the plant runs 250 days/yr and the TWA is 1 mg/m^3
- **THEN** the average daily concentration is 0.5 x 250 over 365 mg/m^3

#### Scenario: Lifetime scaling
- **WHEN** the tenure is 40 years and the lifetime is 78 years
- **THEN** the lifetime average concentration is the average daily one times 40 over 78

#### Scenario: Cancer risk units
- **WHEN** the lifetime average concentration is 0.001 mg/m^3 and the IUR is 1e-6 per ug/m^3
- **THEN** the cancer risk is 1e-6

#### Scenario: Missing toxicity value
- **WHEN** the IUR is not given
- **THEN** the cancer risk is null and the hazard quotient is still computed from the RfC

### Requirement: Occupational risk tier
The system SHALL classify the result as "exceedance" when the limit ratio is above 1, the hazard quotient above 1 or the cancer risk above 1e-4; otherwise "elevated" when the ratio is above 0.1, the hazard quotient above 0.1 or the cancer risk above 1e-6; otherwise "acceptable". A quantity that is null SHALL not count, and when all three are null the tier SHALL be null, not "acceptable". Thresholds come from configuration.

#### Scenario: Exceedance by the limit
- **WHEN** the ratio is 1.2 and the others are below their thresholds
- **THEN** the tier is "exceedance"

#### Scenario: Elevated by cancer risk
- **WHEN** the cancer risk is 5e-6 and the ratio and hazard quotient are below 0.1
- **THEN** the tier is "elevated"

#### Scenario: Acceptable
- **WHEN** all three are present and below their lower thresholds
- **THEN** the tier is "acceptable"

#### Scenario: Nothing to compare
- **WHEN** there is no limit, RfC or IUR
- **THEN** the tier is null
