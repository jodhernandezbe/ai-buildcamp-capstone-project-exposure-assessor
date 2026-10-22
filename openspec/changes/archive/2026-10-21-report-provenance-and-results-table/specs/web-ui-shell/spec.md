## MODIFIED Requirements

### Requirement: Executive summary ribbon
The top of the left pane SHALL show four cards updated from each `workspace_update` event:
1. HQ and cancer risk: highest worst-case and representative values with a status pill
   (green below, amber near, red above the threshold of concern, each also labelled in words);
2. Chemical and read-across provenance: name (when the state has one; otherwise the CAS number stands alone, never a name from elsewhere), CAS, molecular weight, RfC/IUR with sources, and a badge
   "Direct TRI match", "Read-across surrogate" (surrogate CAS/name, hybrid score, cosine,
   Tanimoto, in/out of applicability domain), "Unresolved" or "Not evaluated";
3. Exposed population: total within the radius `r` km and a horizontal stacked bar of the age
   bands 0-4, 5-17, 18-64, 65+, with the data source;
4. Meteorology: the facility it is for (or, for a point that is not one of the facilities, its
   coordinates and that fact), wind speed (m/s), a direction arrow pointing downwind with the from-direction in
   degrees, ambient temperature (K), Pasquill-Gifford class and source.
Cards whose data comes from a screening default SHALL show a "screening default" marker.

#### Scenario: Surrogate badge
- **WHEN** the state reports a read-across surrogate within the domain
- **THEN** card 2 shows the surrogate badge with its hybrid score and "within applicability domain"

#### Scenario: Default weather
- **WHEN** meteorology's source is the screening default
- **THEN** card 4 shows the screening-default marker

#### Scenario: Chemical name
- **WHEN** the state's chemical has a name
- **THEN** card 2 shows it before the CAS number; when it has none, card 2 shows the CAS number only

## ADDED Requirements

### Requirement: Results table in the Overview panel
Below the ribbon, the Overview panel SHALL show a table built only from the workspace state, one row per facility the state holds, with: name and FRS ID, state, emission rate (g/s), screening outcome (fully assessed, worst case only, screened out on the bound or with its own stacks, not assessed), stack tier, worst-case and representative HQ and cancer risk (ranges over the stacks, "not reported" when absent), residents within the radius, and the status pill. Rows SHALL be ordered by the status then the worst-case HQ, highest first, with a column-header sort the user can change; screened-out and unassessed facilities SHALL sit in a folded group below the assessed ones with their count, and a facility's screening value SHALL show in place of its HQ when it was screened out. Selecting a row SHALL open that facility on the map. The table SHALL use tabular numerals, scroll horizontally in a narrow panel, and SHALL never compute or convert a value.

#### Scenario: Every facility present
- **WHEN** the state holds 1,231 facilities of which 157 were assessed
- **THEN** the table lists all 157 assessed rows and a folded group "1,074 screened out or not assessed"

#### Scenario: Sorted by risk
- **WHEN** the table first renders
- **THEN** facilities above concern come first, each group by worst-case HQ descending

#### Scenario: Screened-out row
- **WHEN** a facility was screened out on the bound at HQ 0.05
- **THEN** its row shows "screened out (bound HQ 0.05)" and no representative values

#### Scenario: Row opens the facility
- **WHEN** the user activates a row
- **THEN** the map frames that facility and its card opens
