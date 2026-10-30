## ADDED Requirements

### Requirement: The summary ribbon shows the driving scenario
For each pathway and quantity that has a scenario the ribbon SHALL show the driving scenario by rendering its generic shape: the value and tier, the facility, its factors grouped as source, release, conditions and receptor model, and its most affected receptors (or the reason there are none), instead of listing every facility, stack or population. A pathway added later SHALL be shown without display code of its own. Other facilities SHALL be reachable through an explicit control that is closed by default. An absent factor SHALL read "not reported" with its reason.

#### Scenario: Driver shown
- **WHEN** a run has assessed facilities
- **THEN** each result shows only its driving scenario and a closed control for the others

#### Scenario: Nobody at the maximum
- **WHEN** a community scenario has no receptors
- **THEN** the reason it gives is shown in place of the receptors

#### Scenario: Others on request
- **WHEN** the user opens the control for the others
- **THEN** the other facilities are listed by value, each selectable

### Requirement: The facility inspector shows the worst-case scenario first
The inspector SHALL show a facility's worst-case scenarios before any list of stacks, with the stack that drives each marked in that list, and SHALL show the receptors of the community scenario with their age bands, distance and bearing. The other stacks SHALL stay in a section that is closed when the scenario names one.

#### Scenario: Driving stack marked
- **WHEN** a facility has three stacks and stack 2 drives the hazard quotient
- **THEN** the scenario names stack 2 and the stack list marks it

### Requirement: The map marks the driving facility and its receptors
The map SHALL mark the driving facility of the selected result, and when that facility is selected SHALL draw its listed receptors at their bearing and distance, without drawing the receptors of other facilities. Receptors SHALL be drawn at the coordinates the tool returned, never at a position computed in the browser, only for the results the pinned facility drives, and a tract several results name SHALL be drawn once.

#### Scenario: Receptors drawn
- **WHEN** the driving facility is pinned
- **THEN** its listed receptors are drawn at the coordinates the tool gave

#### Scenario: Receptors removed
- **WHEN** the facility is unpinned or closed
- **THEN** no receptor is drawn

## MODIFIED Requirements

### Requirement: Risk by group has an exposure pathway dropdown
The Risk by group view SHALL have one dropdown, above its three sections, that chooses the exposure pathway as medium, route and receptor: "Outdoor Air → Inhalation → General Population" (the default, the community result) or "Indoor Air → Inhalation → Worker" (the worker result). The choice SHALL apply to the three sections and be kept while the user goes to the summary and back. On the indoor pathway the quantity switch SHALL offer the worker hazard quotient, the worker lifetime cancer risk and the 8-hour average over the occupational limit, each bar being the highest value among the group's assessed facilities at the baseline ventilation, and the dashed lines SHALL be the worker tier boundaries from the client settings; the tooltip SHALL give the facility and its 8-hour average. A bar's tooltip SHALL name the facility and stack that drive it. A facility with no worker value SHALL not be ranked, and a chart with nothing to rank SHALL say why. Leaving the indoor pathway while the limit ratio is shown SHALL return to the hazard quotient.

#### Scenario: Default
- **WHEN** the Risk by group view opens
- **THEN** it has one pathway dropdown, on the outdoor air pathway, and every section shows what it showed before

#### Scenario: Indoor air
- **WHEN** the user chooses the indoor air pathway
- **THEN** all three sections rank the worker values, with the worker boundaries drawn

#### Scenario: Limit ratio only for workers
- **WHEN** the outdoor air pathway is chosen
- **THEN** the limit ratio is not offered

#### Scenario: Nothing to rank
- **WHEN** no facility has a worker value
- **THEN** the chart says why, with no zero bars

#### Scenario: Bar names its driver
- **WHEN** the user hovers a bar
- **THEN** the tooltip names the facility and the stack that give its value
