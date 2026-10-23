# facility-assessment-tool Specification

## Purpose
TBD - created by archiving change batch-facility-assessment. Update Purpose after archive.

## Requirements

### Requirement: Tiered screening of every facility
By default the tool SHALL screen every facility of the chemical's inventory (for the place given), not only the largest emitters, in three tiers:
1. **Bound:** each facility's worst-case hazard quotient and cancer risk with the EPA global default stack, over the SCREEN3 weather combinations and the configured screening ambient temperatures, scaled by its emission rate; computed once per call per unit emission rate, with no request per facility.
2. **Own stacks, worst case:** every facility whose bound reaches the configured HQ threshold or the configured cancer-risk threshold gets its stacks (in evidence order, the global default stack last, so every one has stacks) and its worst case over the same weather combinations and temperatures, with no cap on how many (a configured safety bound, far above any chemical's inventory, may stop it, and then the facilities beyond it SHALL be listed as not assessed with that reason and a warning, never silently).
3. **Full:** the facilities whose own-stack worst case still reaches a threshold, highest worst-case risk first (HQ, then cancer risk), up to `max_facilities`, also get the weather at the site, the residents and the representative case.
A facility below both thresholds at tier 1 or tier 2 SHALL be screened out with its bound and the reason. Facilities screened in but beyond the full-assessment cap SHALL keep their own-stack worst case, labelled as worst case only. When the chemical has neither an RfC nor an IUR, nothing can be screened out: the facilities go to tier 2 and tier 3 by emission rate and the result says why. When FRS IDs are given, those facilities SHALL be assessed without screening, the first `max_facilities` in the order given with the full chain and the rest at their own-stack worst case, labelled worst case only; facilities asked for but not in the inventory SHALL be listed as not assessed. A facility SHALL be left not assessed only for a stated reason (no fallback exists, it is not in the inventory, or the safety bound was reached), and every such facility in the inventory SHALL be returned to the program with that reason. An invalid CAS number SHALL assess nothing and say why.

#### Scenario: A small emitter is screened out with its bound
- **WHEN** a facility's bound HQ is below the HQ threshold and it has no cancer bound at or above the risk threshold
- **THEN** it is screened out at tier 1 with its bound, and no request is made for it

#### Scenario: Ranked by risk, not by emissions
- **WHEN** a facility with a lower emission rate has a higher own-stack worst-case HQ than a larger emitter
- **THEN** it is fully assessed before the larger emitter

#### Scenario: Refined below the threshold
- **WHEN** a facility's bound reaches the threshold but its own-stack worst case does not
- **THEN** it is screened out at tier 2 with its own-stack worst case

#### Scenario: Beyond the full-assessment cap
- **WHEN** more facilities stay above a threshold than `max_facilities`
- **THEN** the rest keep their own-stack worst case, labelled worst case only, and the result counts them

#### Scenario: No benchmark
- **WHEN** the chemical has neither an RfC nor an IUR
- **THEN** no facility is screened out and the result says screening was not possible

#### Scenario: Facilities by ID
- **WHEN** FRS IDs are given, one of them not in the inventory
- **THEN** the others are fully assessed in the order given and the missing one is listed with the reason

#### Scenario: Every candidate is refined
- **WHEN** 700 facilities have a bound at or above a threshold
- **THEN** all 700 get their stacks (the global default when nothing better exists) and their own-stack worst case, and none is listed as not assessed for a limit on how many are refined

#### Scenario: Safety bound reached
- **WHEN** more facilities reach a threshold than the configured safety bound
- **THEN** those beyond it are returned as not assessed with the reason "more than N facilities reach a threshold", and a warning says so

#### Scenario: Facilities by ID beyond the full-chain cap
- **WHEN** 30 FRS IDs of inventory facilities are given and `max_facilities` is 25
- **THEN** the first 25 are fully assessed and the other 5 keep their own-stack worst case, labelled worst case only, and none is listed as not assessed

### Requirement: Stacks in evidence order, never missing
For each facility the tool SHALL use its NEI stack candidates when it has EIS IDs with NEI rows; otherwise the PSTK stacks of the SCC processes that match its industry title with a similarity at or above a configured floor, distinct values only, at most a configured number, evaluated as a range; otherwise the EPA global default stack. The industry title SHALL come from the inventory record, else from the facility's TRI submission. Each facility SHALL carry its stack tier and notes saying why a better source could not be used.

#### Scenario: Own stacks
- **WHEN** the facility has EIS IDs with NEI rows
- **THEN** its NEI candidates are evaluated and no SCC search is made

#### Scenario: Process-typical stacks
- **WHEN** the facility has no EIS registration and its industry matches SCCs above the floor with PSTK rows
- **THEN** up to the configured number of distinct PSTK stacks are evaluated, the SCCs are named and the note says why NEI was not used

#### Scenario: Generic stack
- **WHEN** no SCC matches closely enough, none has a PSTK row, or the industry is unknown
- **THEN** the global default stack is evaluated and the notes say why and that it is generic

### Requirement: Benchmarks given or looked up
The tool SHALL use the RfC and IUR passed to it (for example a read-across surrogate's) and otherwise the chemical's own from CompTox, reporting which, with a warning when a benchmark is missing.

#### Scenario: Surrogate values
- **WHEN** toxicity values are passed
- **THEN** they are used and CompTox is not asked

### Requirement: Concurrent, in the run's context
Facilities SHALL be refined (tier 2) and assessed (tier 3) a configured number at a time, each in a copy of the caller's context so the run's service keys reach every request, with the results in the order selected. The SCC search SHALL be serialized and made once per industry title in a call. A facility's tier-2 stacks SHALL be reused at tier 3. Facilities in the same reanalysis grid cell (the configured cell size) and year SHALL share one weather request in a call. An error that is not a data or network problem SHALL be raised.

#### Scenario: One weather request per grid cell
- **WHEN** two fully assessed facilities lie in the same grid cell and year
- **THEN** the weather is requested once

#### Scenario: Keys reach every facility
- **WHEN** the run holds a service key in a context variable
- **THEN** every facility's steps see it

### Requirement: Two views
The model SHALL receive a compact summary: the benchmarks used and their source, the screening thresholds, how many facilities were found, screened out at each tier (with the highest bound screened out), assessed in full and kept at worst case only, the count per stack tier, and per fully assessed facility its identity, emission rate, stack tier and count, SCCs, industry, weather source, residents and radius, the worst-case and representative ranges of concentration, HQ and cancer risk, and at most a configured number of deduplicated notes, highest worst-case HQ first; per worst-case-only facility (at most a configured number, the rest counted) its identity, emission rate, stack tier and worst-case HQ and cancer risk; plus the facilities not assessed. The program SHALL receive every assessed facility's complete chain, every screened-out facility's record and bound, and every not-assessed facility with its reason, as the artifact.

#### Scenario: Summary only to the model
- **WHEN** the tool returns
- **THEN** the model's text has no stack lists and no screened-out facility list, and the artifact has every assessed facility's stacks and exposure (with weather and residents when fully assessed) and every screened-out facility's bound

#### Scenario: Not assessed travel to the program
- **WHEN** a facility of the inventory is left not assessed
- **THEN** the artifact lists it with its FRS ID and reason, though the model's text only counts and lists them as before

### Requirement: Description guides the use
The description SHALL say what the tool does (it screens every facility of the inventory, and what each tier means), what it needs and what it returns, to report every fully assessed facility and the worst-case-only ones rather than a sample, and the screening counts and thresholds, to give FRS IDs only when the user asks about particular facilities, what each stack tier means (and that the generic default must be stated), that the CAS number is never recalled from a name, and that results are screening estimates.

#### Scenario: Description content
- **WHEN** the description is read
- **THEN** it contains each of the points above
