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

#### Scenario: Click pins the card
- **WHEN** the user clicks a marker
- **THEN** its card stays open after the pointer leaves, its sections can be folded and unfolded, and it closes by its close control, by Escape or by a click on the map

#### Scenario: Pinned card is not replaced by hovering
- **WHEN** one facility's card is pinned and the pointer moves over another marker
- **THEN** the pinned card stays and the other facility's card does not open

### Requirement: Risk by industry, condition of use and life cycle stage
Below the summary ribbon, the Overview panel SHALL show three bar-chart sections, one grouping the facilities by NAICS 3-digit subsector (code and title), one by TSCA condition of use (life cycle stage and COU category), and one by TSCA life cycle stage. Each SHALL show the top five groups on the x-axis with two bars per group: the highest worst-case hazard quotient and the highest worst-case lifetime cancer risk among the group's fully assessed facilities, both unitless, each on its own logarithmic axis (hazard quotient on the left, cancer risk on the right, so each bar is measured from a baseline that means something for its own quantity), with the configured thresholds of concern drawn as dashed reference lines on the axis of their quantity. A group's value SHALL be one of the values the API sent for a facility (a selection, never a sum, mean or conversion), and a facility with no worst-case value, or screened out, SHALL not contribute to it. The groups SHALL be ranked by the highest hazard quotient, or by the highest cancer risk when the user switches the ranking, ties broken by the group label; a group with no value for the ranking quantity SHALL not be ranked. A facility with several conditions of use SHALL appear in each of them, and that section SHALL say so. Hovering or focusing a bar SHALL show the group, the value, the facility it comes from, that facility's worst-case concentration (µg/m³), and the number of facilities in the group with how many of them were assessed. Every bar SHALL also be available as text (a visually hidden table), and a section with nothing to rank SHALL say why instead of showing an empty chart.

#### Scenario: Two bars per group
- **WHEN** the workspace has assessed facilities in three industries
- **THEN** the industry section shows those groups with a hazard-quotient bar and a cancer-risk bar each, and the threshold lines

#### Scenario: Top five
- **WHEN** there are eight groups with values
- **THEN** only the five highest by the chosen ranking are shown

#### Scenario: Value is a selected one
- **WHEN** a group has two assessed facilities with worst-case HQ 2 and 5
- **THEN** its bar is 5 and no combined figure is shown

#### Scenario: Hover details
- **WHEN** the user hovers or focuses a group's hazard-quotient bar
- **THEN** a tooltip names the facility, its worst-case concentration in µg/m³, and "n facilities, m assessed"

#### Scenario: Several conditions of use
- **WHEN** a facility has two conditions of use
- **THEN** it counts in both groups of the condition-of-use section, which notes that facilities can appear in several bars

#### Scenario: Ranking switch
- **WHEN** the user switches the ranking to cancer risk
- **THEN** the groups are reordered and re-cut to the top five by cancer risk

#### Scenario: Nothing assessed
- **WHEN** no facility has a worst-case result
- **THEN** each section says that nothing was assessed yet, with no empty chart

#### Scenario: Unknown industry
- **WHEN** a facility has no subsector
- **THEN** it is not in any industry group and the section counts it as "industry not reported"

### Requirement: Expandable chart sections
Each of the three chart sections SHALL have a control with an accessible name ("Expand section" / "Restore section") that makes it fill the Overview panel's area, hiding the other sections without unmounting them, and restoring the previous layout on the same control or Escape. Escape SHALL close an open inspector or drawer first. In a wide panel the sections SHALL sit side by side and in a narrow one stack, by the panel's width, without horizontal page scroll.

#### Scenario: Expand and restore
- **WHEN** the user expands the industry section and then restores it
- **THEN** it fills the panel while expanded, the summary ribbon and the other sections are hidden but mounted, and the layout returns as before

#### Scenario: Escape
- **WHEN** a section is expanded and no inspector or drawer is open and the user presses Escape
- **THEN** the section is restored

#### Scenario: Panel width
- **WHEN** the panel is narrow
- **THEN** the sections stack vertically and each chart fits the width

## REMOVED Requirements

### Requirement: Results table in the Overview panel
**Reason**: The map and its facility cards already give each facility's details (hover a marker, click it to pin), and the risk charts summarise where the risk sits, so the table duplicated them.
**Migration**: Use the facility map: hover or keyboard-focus a marker for its card, click the marker to pin the card. The Overview panel keeps the summary ribbon and the three risk-by-group charts.
