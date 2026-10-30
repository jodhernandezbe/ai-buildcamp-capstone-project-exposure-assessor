## ADDED Requirements

### Requirement: The configuration behind the worst-case ratio
The worker result SHALL carry for each ventilation tier its label, airflow (m^3/s) and mixing factor with its 8-hour average, limit ratio, hazard quotient, cancer risk and tier, and SHALL carry the fugitive release and its reporting year, the working days per year and hours per shift used, and the occupational limit with its source, so that the worker scenario, which uses the worst-case ventilation tier, can be stated without further computation.

#### Scenario: Both tiers carry their configuration
- **WHEN** the worker result is read
- **THEN** each ventilation tier states its airflow and mixing factor beside its values

#### Scenario: No limit
- **WHEN** the chemical has no occupational limit
- **THEN** the limit ratio is absent, the other quantities are still given, and the reason is carried
