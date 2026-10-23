## MODIFIED Requirements

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


### Requirement: Two views
The model SHALL receive a compact summary: the benchmarks used and their source, the screening thresholds, how many facilities were found, screened out at each tier (with the highest bound screened out), assessed in full and kept at worst case only, the count per stack tier, and per fully assessed facility its identity, emission rate, stack tier and count, SCCs, industry, weather source, residents and radius, the worst-case and representative ranges of concentration, HQ and cancer risk, and at most a configured number of deduplicated notes, highest worst-case HQ first; per worst-case-only facility (at most a configured number, the rest counted) its identity, emission rate, stack tier and worst-case HQ and cancer risk; plus the facilities not assessed. The program SHALL receive every assessed facility's complete chain, every screened-out facility's record and bound, and every not-assessed facility with its reason, as the artifact.

#### Scenario: Summary only to the model
- **WHEN** the tool returns
- **THEN** the model's text has no stack lists and no screened-out facility list, and the artifact has every assessed facility's stacks and exposure (with weather and residents when fully assessed) and every screened-out facility's bound

#### Scenario: Not assessed travel to the program
- **WHEN** a facility of the inventory is left not assessed
- **THEN** the artifact lists it with its FRS ID and reason, though the model's text only counts and lists them as before
