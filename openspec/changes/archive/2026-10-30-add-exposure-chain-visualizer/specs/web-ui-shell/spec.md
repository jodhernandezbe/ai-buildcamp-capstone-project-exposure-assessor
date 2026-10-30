## ADDED Requirements

### Requirement: Overview has an Exposure chain tab
The Overview SHALL offer a third tab, "Exposure chain", beside Summary and Risk by group, showing the
exposure diagram of the focused facility. Summary and Risk by group SHALL be unchanged, and the diagram
SHALL keep its selection while the user switches tabs.

#### Scenario: Third tab
- **WHEN** the user opens the Overview
- **THEN** the switch offers Summary, Risk by group and Exposure chain

#### Scenario: State kept
- **WHEN** the user opens a node's detail, switches to Summary and back
- **THEN** the same node's detail is still open

### Requirement: Pinning a facility focuses it
Pinning a facility on the map (a click on its marker) SHALL report that facility to the application so the
Exposure chain tab can show it. Hovering and unpinning SHALL NOT change the focus.

#### Scenario: Pin
- **WHEN** a marker is clicked
- **THEN** the Exposure chain tab shows that facility

#### Scenario: Hover only
- **WHEN** a marker is only hovered
- **THEN** the diagram does not change
