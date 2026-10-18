## Context

See proposal.md. Inputs the tool receives, as the tools now produce them:
- `emission_rate` (g/s) from `query_emissions_inventory` (annual release over 8,760 h/yr).
- `stack_params`: one `StackParameters` (m, m, m/s, K), a candidate of `fetch_stack_parameters_from_nei` or the tier-2 result; any value may be null.
- `meteorology`: annual mean 10 m wind speed (m/s), prevailing direction, modal stability class, mean ambient temperature (K), `source`, `warnings` (`get_meteorological_boundary`).
- `population`: residents and age mix (0-4, 5-17, 18-64, 65+ percent), `source`, `warnings`.
- `toxicity`: `rfc` (mg/m^3) and `iur` ((ug/m^3)^-1) from `fetch_chemical_properties`, where either can be null.

What `models/` already has: `calculate_dispersion_coefficients` (Briggs open-country fits for A to F, valid 100 m to 10 km), `gaussian_plume` (ground reflection, g/m^3), `average_daily_dose`, `calculate_hazard_quotient`, `calculate_cancer_risk`. What it lacks: plume rise, wind adjustment to stack height, any search over weather and distance, and exposure concentration.

EPA's SCREEN3 user's guide (checked, EPA-454/B-95-004) gives the reference procedure. Verified in it: "full meteorology" evaluates 54 combinations of stability class and 10 m wind speed (A: 1, 1.5, 2, 2.5, 3; B: 1 to 5 in 0.5 steps; C: 1 to 5 in 0.5 steps, 8, 10; D: 1 to 5 in 0.5 steps, 8, 10, 15, 20; E: 1 to 5 in 0.5 steps; F: 1 to 4 in 0.5 steps, m/s); the "automated distance array" has 50 distances, 100 m steps to 3,000 m, 500 m steps to 10 km, 5 km steps to 30 km and 10 km steps to 50 km (verified); the 10 m winds are adjusted to stack height by a power law (not adjusted for releases below 10 m); the buoyancy flux is Fb = g vs ds^2 (Ts - Ta) / (4 Ts); stack-tip downwash follows Briggs (1973); final plume rise is used for simple terrain; results are maximum 1-hour concentrations and a 24-hour factor of 0.4 is quoted. Not in that guide (it points to the Screening Procedures document EPA-454/R-92-019 and ISC3 Volume II): the plume-rise formulas' constants, the wind-profile exponents, the annual factor. Those are task 0.

## Goals / Non-Goals

**Goals:**
- A defensible EPA-style screening concentration, dose and risks, with the method's limits stated and no invented defaults.
- Pure, testable models; configuration for every constant, each with a source.
- A system prompt that matches the tools and cannot silently drift from the registry.

**Non-Goals:**
- Building downwash, terrain, fumigation, mixing-height limits, multiple sources, deposition, chemistry, wind-direction-resolved or population-located concentrations.
- The AERMOD/AERSCREEN approach (a different model family with its own preprocessors).
- Changing the other tools beyond `ExposureMetrics`/`Toxicity` types.

## Decisions

**D0. Distances stop at 10 km.** `models/dispersion.py` documents its Briggs open-country coefficients as valid for 100 m to 10 km, while SCREEN3's array runs to 50 km using the ISC3 curve fits (ISC3 Volume II, not available). Extrapolating the Briggs fits to 50 km would present an extrapolation as EPA's method, so the default array is SCREEN3's own, truncated at 10 km: 100 m steps to 3,000 m and 500 m steps to 10 km, 44 distances. The search raises `ValueError` for a distance outside the validity range of the dispersion model, so a settings change cannot silently extrapolate. Consequence: a tall stack whose maximum would fall beyond 10 km is understated (the result then sits at the last distance, which the warnings state). Extending the range needs the ISC3 far-field coefficients and is a follow-up.

**D1. Method: SCREEN3-style search.** For every (class, 10 m speed) combination in the configured grid and every configured distance, compute the effective release height (stack height with stack-tip downwash plus final plume rise at the stack-height wind), the Briggs rural sigma_y and sigma_z at the distance, and the ground-level centerline concentration with ground reflection (`gaussian_plume` with y = 0, z = receptor height); the maximum over all pairs is the screening result, with its combination, distance and release height. 54 x 44 = 2,376 evaluations, vectorized with numpy. Dispersion is rural (open-country), flat terrain, no inversion lid.

**D2. Two scenarios.** The headline is the grid maximum (EPA's worst case). The representative scenario evaluates only the meteorology tool's (class, speed) pair over the same distances, with the same ambient temperature; it is reported beside the headline so a user sees the spread. The ambient temperature input is used for plume rise in both; if the meteorology input is the labelled screening default the representative scenario is still computed and a warning says it is generic.

**D3. Averaging.** SCREEN3 gives 1-hour maxima. Chronic benchmarks (RfC, IUR) need long-term averages, so the 1-hour maximum is multiplied by the annual factor 0.08 of EPA's Screening Procedures (EPA-454/R-92-019, section 4.2 step 5: 3 h 0.9, 8 h 0.7, 24 h 0.4, annual 0.08, each with a stated tolerance; verified). The result reports both the 1-hour and the annual concentration; the hazard quotient and cancer risk use the annual one.

**D4. Exposure concentration approach for HQ and cancer risk.** EPA's inhalation risk approach (RAGS Part F): EC = C x ET/24 x EF/365 x ED/AT; HQ = EC (ug/m^3) / (RfC x 1,000); cancer risk = EC_lifetime x IUR, with the cancer averaging time 70 years. These are independent of age, because the RfC and IUR are concentrations, not doses. The age-band doses (`average_daily_dose`: C x IR x EF x ED / (BW x AT) with each band's inhalation rate and body weight) are reported separately because a dose is what differs by age (children breathe more per kilogram); the highest band is named. This is stated in the description so nobody reads the band doses as band-specific risks.

**D5. Exposure factors and their sources.** Defaults in `[exposure]` with the source in a comment: exposure time 24 h/day, frequency 350 days/yr, duration 26 years, cancer averaging time 70 years (verified: EPA RSL User's Guide, section 6, Table 1, resident air), and, per band, the mean long-term inhalation rate (m^3/day, EFH 2011 Table 6-1) and mean body weight (kg, EFH 2011 Table 8-1) of one handbook age group. Bands: 0-4, 5-17, 18-64, 65+, matching the population tool. The handbook's groups are finer than the bands, so one rule picks the group: the group inside the band with the highest inhalation rate per kilogram of body weight, which is the conservative choice for a screening dose (0-4: 1 to <2 years, 8.0 and 11.4; 5-17: 3 to <6 years, 10.1 and 18.6, the group holding age 5; 18-64: 16 to <21 years, 16.3 and 71.6, the group holding 18 to 20; 65+: 61 to <71 years, 14.2 and 80.0). The rule and the group are written beside each value in the settings; a year-weighted mean would be the representative alternative.

**D6. Layers.** `models/plume_rise.py` (buoyancy flux, final rise, downwash), `models/wind_profile.py` (power law), `models/screening.py` (the search; takes the combinations, distances and per-class parameters as arguments, not constants), `models/exposure.py` (exposure concentration, band doses, HQ, cancer risk on top of `dose.py`/`risk.py`). `config/exposure.py`: `ExposureSettings`. `tools/exposure/helpers/assessment.py`: input validation, both scenarios, warnings, result assembly. `tools/exposure/metrics.py`: the `@tool`. All functions at most 18 body lines; gravitational acceleration is a physical constant in the plume-rise model, not a setting.

**D7. Result shape.** `ExposureMetrics`: the headline `max_concentration` (ug/m^3, the annual average at the worst case), `max_concentration_1h`, `distance_m`, `stability_class`, `wind_speed` (10 m, m/s), `effective_release_height`, `hq`, `cancer_risk`, `add` (highest band dose, mg/kg-day), `add_band`, `add_by_band`, a nested `representative` block (the same fields for the representative scenario) and `warnings`. All numbers are `float | None`. The old names `max_concentration`, `add` and `hq` keep their meaning (worst case, highest band).

**D8. Failure policy.** No defaults. An invalid or missing input nulls what depends on it and adds a warning naming it; the rest is still returned (a null IUR does not stop the hazard quotient). Zero emission is a valid input giving zeros. A bad configuration raises at load. A stack with any null value gives null concentrations and a warning pointing to the tier-2 tool. This is deliberately different from the meteorology and population tools, which return a labelled default: there is no defensible default for a concentration, and an invented one would look like a result.

**D9. Types.** `Toxicity.rfc` and `.iur` become `float | None` (additive), because `fetch_chemical_properties` returns null for values it could not obtain. `ExposureMetrics` is extended as in D7.

**D10. The system prompt teaches the process; the tool descriptions carry the decisions.** A prompt that names tools and an order of calls ("first X, then Y") breaks as soon as a tool is added or the question changes, and it moves tool-specific knowledge to the wrong place. `prompts/agent_system.md` therefore describes how an exposure assessor works: the chain of links (chemical and toxicity, sources, transport, receptors, exposure and risk), the quality of evidence (facility-specific, process-typical, generic default) and the habit of using the best available and disclosing the rest, screening conservatism, evaluating alternatives and reporting a range, never inventing numbers, stopping a branch that has no defensible answer, and asking the user only for what no tool can supply. It was rewritten ahead of this change (see the file) and is guarded by `tests/prompts/test_agent_system.py`: no registered tool name, no snake_case call-like identifier, no numbered step list, the four XML sections in order, and the quality-signal and Limitations wording present. What the agent needs to know about a tool (when it applies, what a null or a `source` or a `warnings` entry means, which situation calls for another tool, that a fallback is used only when the better source returned nothing) lives in that tool's description; task 3.5 audits every description against this and fixes the gaps, including the new exposure tool's.

## Risks / Trade-offs

- [Constants verified.] The annual factor, Briggs constants, downwash, wind exponents and stability gradients come from EPA-454/R-92-019 (section 3 and 4.2), the exposure factors from the RSL User's Guide Table 1, and the age-band rates and weights from EFH 2011 Tables 6-1 and 8-1; each is cited in the settings. ISC3 Volume II was not reachable, so the plume-rise regime boundary (Fb = 55) and the use of final rise rely on the Screening Procedures text.
- [Maximum at the edge of the range.] When the worst case falls at the last distance (10 km) the true peak may be farther; the result says so in a warning.
- [The peak may be where nobody lives.] SCREEN3's maximum is over 100 m to 50 km regardless of population; pairing it with a nearby population is conservative and says nothing about who is at the peak. Stated in the warnings. A population-aware variant is a possible follow-up.
- [No mixing-height limit.] Unstable cases under an inversion lid are underestimated by this model (SCREEN3 includes it); a documented limitation.
- [Final rather than transitional plume rise] follows SCREEN3 for simple terrain, but overstates rise near the stack, understating nearby concentrations.
- [Rural coefficients everywhere.] Urban sites would need the urban set; not modeled.
- [A 1-hour to annual factor is crude.] It is the EPA screening factor, not a long-term model; the description says so.
- [The meteorology tool's representative values are annual means.] The representative scenario is context, not a conservative bound.
- [Dependence on the prompt test.] The guard only checks names, not wisdom; reviewing the prompt text stays a human task.
