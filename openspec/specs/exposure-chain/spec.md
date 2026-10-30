# exposure-chain Specification

## Purpose

An interactive diagram of how a facility's worst-case exposure arises, from release to the metric a
person is judged against, built from pathway lanes that can be added without changing the diagram.

## Requirements

### Requirement: Diagram of worst-case connections
The tab SHALL draw, for the focused facility, a facility hub and one lane per registered pathway, each
lane running source, pathway, route, receptor and endpoint with a connection between consecutive steps.
Each connection SHALL be labelled with the quantity it carries and each node SHALL show its headline
value. Every value, name and status SHALL come from the API; the browser SHALL NOT compute, convert or
estimate any of them. A value the API did not report SHALL read "not reported" with its reason, never 0
or "-". With no facility the tab SHALL say what to do instead of drawing placeholders.

#### Scenario: Community lane
- **WHEN** the facility has a community result
- **THEN** the lane shows the stack release, outdoor air with the peak concentration and distance, inhalation, the residents counted with their age bands, and the worst-case hazard quotient and cancer risk

#### Scenario: Worker lane
- **WHEN** the facility has an occupational result
- **THEN** the lane shows the fugitive release, indoor workplace air with ventilation and concentration, inhalation, the shift worker with the schedule, and the 8-hour average, limit ratio, benchmark source, hazard quotient, cancer risk and tier

#### Scenario: Missing value
- **WHEN** a value is null (for example no fugitive release)
- **THEN** that node or connection reads "not reported" with the reason and the rest of the diagram is unaffected

#### Scenario: Unavailable lane
- **WHEN** the facility lacks the result a lane needs
- **THEN** the lane is drawn as an empty, labelled lane saying why

#### Scenario: No facility
- **WHEN** the workspace has no facilities
- **THEN** the tab shows an empty state

### Requirement: The diagram draws the graph the API sent
The diagram SHALL draw the facility's exposure graph as sent, laid out automatically left to right, with
any number of lanes, branches and nodes. A new lane, node or edge in the graph SHALL be drawn without a
frontend change. The canvas SHALL pan and zoom and fit the graph to view; it SHALL open at a readable zoom (anchored on the source when the whole graph does not fit) and show a minimap while part of the graph is out of view. Connections SHALL show the direction of flow with moving markers, still when the user prefers reduced motion.

#### Scenario: New lane
- **WHEN** the graph contains a lane the frontend has never seen
- **THEN** it is drawn with its nodes and labelled connections

#### Scenario: Branches
- **WHEN** the graph has several stack nodes and several age-band nodes
- **THEN** each is drawn and connected, without overlap

### Requirement: Every state is checked visually
Each state of the tab (both lanes, missing values, unavailable lane, exceedance, light and dark, wide and
narrow) SHALL be rendered in a real browser by the test suite, and its screenshot SHALL be compared with
the approved reference.

#### Scenario: Layout change
- **WHEN** a change moves or overlaps nodes
- **THEN** the screenshot comparison fails

### Requirement: Explore by hover, focus and click
Hovering or focusing a node SHALL highlight its lane and dim the others; choosing it (click, Enter or
Space) SHALL open a detail panel listing its fields with units, sources, assumptions and warnings as the
API sent them, and for the receptors the dose of each age band; choosing it again or pressing Escape
SHALL close it. The user SHALL be able to isolate one lane and choose the facility. The panel SHALL NOT state anything the data does not show.

#### Scenario: Highlight
- **WHEN** a node is hovered or focused
- **THEN** its lane stays prominent and the other lane is dimmed

#### Scenario: Detail
- **WHEN** the receptor node is chosen
- **THEN** the panel lists the residents, the age-band shares and the dose of each band

#### Scenario: Escape
- **WHEN** the panel is open and Escape is pressed
- **THEN** it closes and a fullscreen panel is not left

#### Scenario: Both ventilation tiers
- **WHEN** the worker endpoint is chosen
- **THEN** the panel lists the worst-case and the baseline values the API sent

### Requirement: Status in words and colour
Status SHALL be taken from the API (below, near or above concern for community values; acceptable,
elevated or exceedance for the occupational tier, relabelled onto the same three looks), shown as words
as well as colour, with design-token colours that meet WCAG AA in light and dark.

#### Scenario: Exceedance
- **WHEN** the occupational tier is exceedance
- **THEN** the endpoint and the lane's connections read it in words and use the "above" look

### Requirement: Follows the facility the user is looking at
The tab SHALL show the facility pinned on the map or chosen in its own picker; when none, the facility
the chat selected. A pin or choice SHALL be dropped when the chat selects a different facility or the
workspace is replaced, and SHALL fall back when its facility is gone.

#### Scenario: Map pin
- **WHEN** the user pins a facility on the map
- **THEN** the diagram shows it

#### Scenario: Chat selection
- **WHEN** the chat selects a different facility
- **THEN** the diagram shows it and the earlier pin is dropped for good

### Requirement: Accessible and responsive
Every node SHALL be a keyboard-focusable control whose accessible name states its step, label and value;
connections SHALL be described in text for screen readers (for example "release to outdoor air: 1 g/s");
the canvas SHALL pan and zoom rather than shrink text below a legible size; flow animation SHALL be
off when the user prefers reduced motion.

#### Scenario: Keyboard
- **WHEN** the user tabs through the diagram
- **THEN** each node takes focus in lane order and Enter opens its detail

#### Scenario: Narrow panel
- **WHEN** the panel is narrower than the diagram
- **THEN** the graph is fitted to the view and can be panned and zoomed

#### Scenario: Reduced motion
- **WHEN** the user prefers reduced motion
- **THEN** the flow animation is not played

### Requirement: Edge labels at a legible size
Quantity labels on the exposure chain's edges SHALL use no text smaller than the design system's
micro-badge step (11 px); the value SHALL be at least the caption size (12 px).

#### Scenario: Edge with a quantity
- **WHEN** an edge carries a quantity
- **THEN** its label renders at 11 px or larger and its value at 12 px or larger
