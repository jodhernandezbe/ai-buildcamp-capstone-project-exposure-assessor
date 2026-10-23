## MODIFIED Requirements

### Requirement: Screening shown per facility
Each facility of a batch assessment SHALL carry its screening outcome: fully assessed, worst case only, screened out at the bound or with its own stacks, or not assessed, with the bound HQ and cancer risk and the reason. A screened-out facility SHALL be placed on the map from its record even when the inventory was not listed. The facility card SHALL say why a facility has no stacks or risk (screened out, with its bound and the threshold; or not assessed, with the reason the assessment gave; or not covered by a batch assessment yet) instead of implying the values are missing, and SHALL say when only the worst case was computed. A not-assessed result SHALL NOT replace a facility's real result, and one for an FRS ID with no placed facility SHALL be ignored.

#### Scenario: Screened-out facility
- **WHEN** a facility was screened out at the bound
- **THEN** its card shows the bound HQ, the threshold and that it was screened out, not "not reported"

#### Scenario: Worst case only
- **WHEN** a facility kept only its own-stack worst case
- **THEN** its card shows its stacks and worst-case risk and says the representative case, weather and residents were not computed

#### Scenario: Not assessed with a reason
- **WHEN** the batch assessment returns a facility as not assessed with a reason
- **THEN** its card says "Not assessed" and the reason, not that stack parameters were not obtained

#### Scenario: Not covered yet
- **WHEN** a facility is on the map from the inventory but no batch assessment has covered it
- **THEN** its card says that no batch assessment has covered it yet
