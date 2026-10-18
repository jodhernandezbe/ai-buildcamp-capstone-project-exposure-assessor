## 0. Verify the constants before coding

- [x] 0.1 Verify in EPA-454/R-92-019 (Screening Procedures; ISC3 Vol. II was not available): annual factor 0.08 (3 h 0.9, 8 h 0.7, 24 h 0.4); Fb = g vs ds^2 (Ts - Ta) / (4 Ts) with g = 9.806 m/s^2 and Ta = 293 K when unknown; unstable/neutral rise u*dh = 21.4 Fb^(3/4) for Fb < 55 and 38.7 Fb^(3/5) otherwise; stable rise dh = 2.6 (Fb / (u s))^(1/3) with s = (g / Ta) d(theta)/dz, 0.02 K/m for E and 0.035 K/m for F; stack-tip downwash h = hs + dh + 2 (vs/us - 1.5) ds when vs < 1.5 us; rural wind exponents A 0.07, B 0.07, C 0.10, D 0.15, E 0.35, F 0.55, none below 10 m
- [x] 0.2 Verified in the RSL User's Guide, section 6, Table 1: ET 24 h/day (resident), EF 350 d/yr, ED 26 yr (6 child + 20 adult), LT 70 yr, AT = 365 x LT (carcinogenic) or 365 x ED (non-carcinogenic)
- [x] 0.3 EFH 2011 Table 6-1 (mean long-term inhalation, m3/day) and Table 8-1 (mean body weight, kg) read; rule: for each band, the EFH age group inside the band with the highest inhalation rate per kilogram (the conservative sub-group), so 0-4 -> 1 to <2 yr (8.0, 11.4), 5-17 -> 3 to <6 yr (10.1, 18.6; age 5), 18-64 -> 16 to <21 yr (16.3, 71.6; ages 18-20), 65+ -> 61 to <71 yr (14.2, 80.0)
- [x] 0.4 Confirmed (tests `test_missing_value_warns`, `rfc is None`): `fetch_chemical_properties` returns `rfc`/`iur` as null when missing, and that the Toxicity input can be built from it

## 1. Configuration

- [x] 1.1 Add `[exposure]` to `config/settings.toml` (weather combinations, distance segments and minimum distance, receptor height, annual factor, per-class exponents and gradients, exposure factors, per-band inhalation rates and body weights) with a source comment on every value
- [x] 1.2 `config/exposure.py`: `ExposureSettings`, loader, cached getter, expanded distance array, validation per the app-configuration delta; tests with a negative case per key and a check that the default file yields 54 combinations and 44 distances from 100 m to 10 km

## 2. Models

- [x] 2.1 `models/plume_rise.py`: buoyancy flux, final rise (unstable/neutral, stable), stack-tip downwash; tests for monotonicity (hotter, stronger wind), zero rise at ambient temperature, regime boundaries, downwash on/off, impossible input, and a hand-computed value per formula
- [x] 2.2 `models/wind_profile.py`: power law with the class exponent, no adjustment below 10 m; tests
- [x] 2.3 `models/screening.py`: the search over combinations x distances using the existing dispersion and plume models; tests for the maximum being attained, linearity in the emission rate, the minimum distance, empty sets, taller stack never increasing the maximum, and a cross-check against an independent brute-force loop
- [x] 2.4 `models/exposure.py`: annual conversion, exposure concentration, band doses, highest band, HQ, cancer risk; tests per spec scenario with hand-computed values

## 3. Tool

- [x] 3.1 Extend `ExposureMetrics` and make `Toxicity` values optional in `tools/schemas.py`
- [x] 3.2 `tools/exposure/helpers/assessment.py`: input validation, both scenarios, per-band doses, null results with warnings, default-status warnings; tests for every scenario of the tool spec (no network)
- [x] 3.3 Replace the stub in `tools/exposure/metrics.py` with the thin tool and the full description; replace the stub test with schema, description and end-to-end tests
- [x] 3.4 Integration test: build the inputs from the real shapes (a candidate from `NeiStackResult`, `Meteorology`, `Population`, `ChemicalProperties`) with synthetic round numbers and run the tool
- [x] 3.5 Audit every tool description against spec "Decisions come from tool descriptions and results": for each of the chemical properties, emissions inventory, both stack, SCC description, meteorology, population and exposure tools, check it states when it applies, what each output and each null, `source` and `warnings` value means, and what situation calls for another tool; fix gaps; add a test per tool for the phrases that carry the decision (for example the fallback condition and the default label)

## 4. System prompt

- [x] 4.1 Rewrite `prompts/agent_system.md` as a description of how an assessor works (no tool names, no call order), per design D10
- [x] 4.2 `tests/prompts/test_agent_system.py`: the four sections in order, no registered tool name, no call-like identifier, no numbered steps, quality-signal and Limitations wording present
- [x] 4.3 After 3.5, read the prompt and every tool description together once end to end for contradictions and for decisions the prompt assumes but no description supports

## 5. Docs and gates

- [x] 5.1 README: the tool implemented, the method and its limits, the sources of the constants
- [x] 5.2 `uv run ruff format .`, `ruff check .`, `pyright`, `bandit`, the function-length check, `pytest` and `pre-commit run --all-files` all pass
- [x] 5.3 `openspec validate implement-exposure-metrics-tool --strict` passes
