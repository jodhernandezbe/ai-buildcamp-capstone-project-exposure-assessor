## ADDED Requirements

### Requirement: Neighbours and workers are reasoned about together
The prompt SHALL explain, as assessment reasoning and without naming a tool or a call order, that people near a plant and people who work in it are exposed differently (a stack release reaches the neighbours through outdoor air; a fugitive release mainly reaches the workers), that the community and the worker results are reported side by side with which one drives the concern at a facility, that the worker figures are a screening with generic ventilation and not a compliance finding, and that a worker figure that could not be computed is reported as not computed with its reason.

#### Scenario: Both audiences
- **WHEN** the prompt is read
- **THEN** it says to report the community and the worker result side by side and to say which drives the concern

#### Scenario: Not a compliance finding
- **WHEN** the prompt is read
- **THEN** it says the worker figures are a screening, not a compliance finding

#### Scenario: Not computed
- **WHEN** the prompt is read
- **THEN** it says a worker figure that could not be computed is reported as not computed, with the reason
