## ADDED Requirements

### Requirement: Scenarios and their drivers in the workspace
The workspace SHALL carry, for each pathway and quantity that has a scenario, the driving facility and its worst-case scenario in the generic shape, and for every assessed facility its scenarios with their receptors, projected from tool results only. A scenario or receptor list that is not valid SHALL be left out alone with a warning. A scenario SHALL never mix values of different facilities or stacks.

#### Scenario: Driver per result
- **WHEN** a run assesses several facilities
- **THEN** the workspace names the driving facility of each result, which may differ from result to result

#### Scenario: Invalid scenario
- **WHEN** one facility's scenario is not valid
- **THEN** it is left out with a warning and the others are kept

#### Scenario: Older server
- **WHEN** the server sends no scenarios
- **THEN** the workspace has none and the dashboard shows the results it showed before
