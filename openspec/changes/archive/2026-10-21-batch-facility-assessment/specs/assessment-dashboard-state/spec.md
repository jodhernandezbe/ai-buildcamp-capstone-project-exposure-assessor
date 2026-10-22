## ADDED Requirements

### Requirement: Batch results attach by FRS ID
Each facility of a batch assessment SHALL be placed on the map from its record and given its stacks (with their tier and SCC), weather, residents and exposure, attached by FRS ID, so facilities with the same emission rate keep their own results. A later single-tool result for a facility SHALL replace the batch one. An invalid facility item SHALL be left out with a warning; a batch result without its details SHALL be skipped with a warning.

#### Scenario: Same emission rate
- **WHEN** two assessed facilities have the same emission rate
- **THEN** each shows its own stacks and risk

#### Scenario: Later single result
- **WHEN** an exposure result for one facility follows the batch result
- **THEN** that facility shows the later result

### Requirement: Screening shown per facility
Each facility of a batch assessment SHALL carry its screening outcome: fully assessed, worst case only, or screened out at the bound or with its own stacks, with the bound HQ and cancer risk and the reason. A screened-out facility SHALL be placed on the map from its record even when the inventory was not listed. The facility card SHALL say why a facility has no stacks or risk (screened out, with its bound and the threshold, or not assessed) instead of implying the values are missing, and SHALL say when only the worst case was computed.

#### Scenario: Screened-out facility
- **WHEN** a facility was screened out at the bound
- **THEN** its card shows the bound HQ, the threshold and that it was screened out, not "not reported"

#### Scenario: Worst case only
- **WHEN** a facility kept only its own-stack worst case
- **THEN** its card shows its stacks and worst-case risk and says the representative case, weather and residents were not computed
