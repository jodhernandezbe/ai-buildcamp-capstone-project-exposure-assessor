## ADDED Requirements

### Requirement: Worker results sit with the community results
The interface SHALL show the worker (occupational) screening wherever it shows the community result, never in a separate view: the Overview summary ribbon, the facility inspector and the map. It SHALL show only values the API sent, and an absent value SHALL read "not reported", never zero.

#### Scenario: No separate view
- **WHEN** the Overview panel is open
- **THEN** it offers the same views as before (Summary and Risk by group) and no view or facility picker for the workers alone

#### Scenario: Not reported
- **WHEN** a facility has no worker result
- **THEN** every worker value of it reads "not reported" and no zero is shown

### Requirement: Worker card in the summary ribbon
The Overview summary ribbon SHALL include a "Worker exposure" card with the highest 8-hour TWA to limit ratio, worker hazard quotient and worker lifetime cancer risk over the assessed facilities, each for the baseline ventilation and the enclosed-zone worst case, with the facility each comes from and its tier in words, in the way the hazard quotient and cancer risk card names its facility. Where nothing is available it SHALL say why.

#### Scenario: Highest values
- **WHEN** several facilities have worker results
- **THEN** each figure is the highest among them and names its facility

#### Scenario: Nothing yet
- **WHEN** no facility has a worker result
- **THEN** the card shows "not reported" for each figure and the reason

### Requirement: Worker section in the facility inspector
The facility inspector (hover and pinned card) SHALL show a compact badge with the community hazard quotient and the worker tier with its limit ratio, so a user can see whether the concern comes from the stack plume or from indoor fugitive release, and a "Worker exposure" section with the facility's operating schedule (days per year, hours per day, hours per year), life cycle stage and condition of use, CDR industrial sector, fugitive release, occupational limit and its source, and for both ventilation tiers the 8-hour TWA, limit ratio, worker hazard quotient and worker cancer risk and the tier, with the warnings. The tier SHALL be written as text as well as coloured.

#### Scenario: Both results
- **WHEN** a facility has a community and a worker result
- **THEN** the badge shows both and the section lists both tiers

#### Scenario: Tier not by colour alone
- **WHEN** a tier is shown
- **THEN** it is written in words

### Requirement: Worker tier on the map
The map SHALL draw a ring around each facility marker coloured by the worker tier (none while it is not computed), keeping the marker fill for the community status and its size for the emission rate; the legend SHALL explain the ring and count the facilities of each tier, and the marker's accessible name SHALL include the worker tier.

#### Scenario: Ring and fill
- **WHEN** a facility is above concern in the community result and elevated for workers
- **THEN** its marker is filled for the community status and ringed for the elevated tier

#### Scenario: No worker result
- **WHEN** no facility has a worker result
- **THEN** no ring is drawn and the legend has no ring entry

#### Scenario: Accessible name
- **WHEN** a marker has a worker tier
- **THEN** its accessible name includes it

### Requirement: Risk by group has an exposure pathway dropdown
Each Risk by group section SHALL have a dropdown in its header that chooses the exposure pathway as medium, route and receptor: "Outdoor Air → Inhalation → General Population" (the default, the community result) or "Indoor Air → Inhalation → Worker" (the worker result). The choice SHALL be shared by the three sections and kept while the user goes to the summary and back. On the indoor pathway the quantity switch SHALL offer the worker hazard quotient, the worker lifetime cancer risk and the 8-hour average over the occupational limit, each bar being the highest value among the group's assessed facilities at the baseline ventilation, and the dashed lines SHALL be the worker tier boundaries from the client settings; the tooltip SHALL give the facility and its 8-hour average. A facility with no worker value SHALL not be ranked, and a chart with nothing to rank SHALL say why. Leaving the indoor pathway while the limit ratio is shown SHALL return to the hazard quotient.

#### Scenario: Default
- **WHEN** the Risk by group view opens
- **THEN** every section is on the outdoor air pathway and shows what it showed before

#### Scenario: Indoor air
- **WHEN** the user chooses the indoor air pathway in one section
- **THEN** all three sections rank the worker values, with the worker boundaries drawn

#### Scenario: Limit ratio only for workers
- **WHEN** the outdoor air pathway is chosen
- **THEN** the limit ratio is not offered

#### Scenario: Nothing to rank
- **WHEN** no facility has a worker value
- **THEN** the chart says why, with no zero bars
