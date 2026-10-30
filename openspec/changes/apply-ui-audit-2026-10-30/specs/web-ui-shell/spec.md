## ADDED Requirements

### Requirement: Empty sections take their content height
A section of the executive summary that has no data SHALL occupy only the height of its content;
grid rows SHALL grow to share the panel only when they hold data. At first load the five summary
cards SHALL be visible without scrolling at the default panel size.

#### Scenario: First load
- **WHEN** the workspace has no scenario drivers
- **THEN** the worst-case section is one line high and the risk, worker, chemical, population and meteorology cards follow directly beneath it

#### Scenario: Scenarios present
- **WHEN** the workspace has scenario drivers
- **THEN** the worst-case section grows with its content as before

### Requirement: Map overlays never escape the map
The map SHALL be its own stacking context: its basemap control, legend, notices and inspector
SHALL never render above a layer that covers the analysis area (the Monitoring view, drawers,
dialogs, a fullscreen panel).

#### Scenario: Monitoring open
- **WHEN** the Monitoring view covers the analysis area
- **THEN** no map control or legend is visible over it

### Requirement: Legend before data
While no facility is mapped, the legend SHALL show one sentence saying so instead of per-status
counts; counts SHALL appear once at least one facility exists.

#### Scenario: No facilities
- **WHEN** the workspace has no facilities
- **THEN** the legend reads "No facilities mapped yet" and shows no counts

#### Scenario: Facilities present
- **WHEN** the workspace has facilities
- **THEN** each status entry shows its count

### Requirement: Disabled controls say why
A disabled navigation action SHALL expose the reason it is disabled both as a tooltip and as an
accessible description.

#### Scenario: Nothing to clear
- **WHEN** the workspace is empty and "Clear workspace" is disabled
- **THEN** the control's accessible description states the reason

### Requirement: Compartment badges in words
The welcome mark's compartment badges SHALL be sentence-case words, with compartments that are not
yet available marked "planned", and SHALL NOT use decorative separators or tracked uppercase.

#### Scenario: Welcome shown
- **WHEN** the conversation is empty
- **THEN** the badges read "Air", "Water (planned)", "Soil (planned)"

### Requirement: Absent age bands are not zero
An age band the API did not report SHALL be omitted from the population bar and listed as "not
reported" beneath it; it SHALL NOT render as a 0 % share.

#### Scenario: Band missing
- **WHEN** the receptors' age distribution lacks a band
- **THEN** the bar shows only the reported bands and the missing band is named as not reported
