## MODIFIED Requirements

### Requirement: Facility inspector popover
Hovering or keyboard-focusing a marker SHALL open a translucent inspector anchored to it, and
it SHALL close on leave, blur or Escape. It SHALL show: facility name, FRS ID, TRI document
control number, NAICS code and title; reported release with its unit, emission rate (g/s),
operating hours (h/yr) and CAS; the TSCA life cycle stages and conditions of use the API sent
(each condition with its TRI activity and COU category), or "not reported" with the API's note
when there are none; each stack's height (m), diameter (m), exit velocity (m/s), exit
temperature (K) with its provenance tier pill; and receptor metrics: worst-case and
representative maximum concentration (µg/m³), HQ, cancer risk and population within the
radius. Markers SHALL be reachable by keyboard and announce the facility name to screen readers.

#### Scenario: Keyboard focus
- **WHEN** a marker receives keyboard focus
- **THEN** the inspector opens for that facility and Escape closes it

#### Scenario: Several stacks
- **WHEN** the facility has three NEI candidates
- **THEN** the inspector lists all three with Tier 1 pills and the HQ range across them

#### Scenario: Several conditions of use
- **WHEN** the facility has conditions in Processing and Industrial use
- **THEN** the inspector lists both stages and each condition with its activity and category

#### Scenario: No conditions
- **WHEN** the facility has no conditions of use
- **THEN** the inspector shows "not reported" with the note, never an empty list that looks like a result
