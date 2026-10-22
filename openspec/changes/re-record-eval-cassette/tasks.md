## 1. Recording

- [ ] 1.1 Confirm `comptox.epa.gov` answers (certificate renewed), then `uv run python -m evals record full-assessment-with-nei-stacks`
- [ ] 1.2 Check the cassette holds `fetch_chemical_properties` with benchmarks and the calls of the route taken; record again if the other route is needed and the recorder can keep it

## 2. Verification

- [ ] 2.1 `uv run pytest -m eval` three times; all checks pass each time; note the judge's verdicts
