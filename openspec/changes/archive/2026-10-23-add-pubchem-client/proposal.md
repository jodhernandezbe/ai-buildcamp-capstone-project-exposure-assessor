## Why

`fetch_chemical_properties` gets every value from CompTox. When CompTox has no molecular weight,
vapor pressure or density for a chemical (or its value fails validation), the field comes back
null and the exposure calculation cannot use it. PubChem often has these values. The agent
should get a second chance at them from PubChem, without ever letting a doubtful PubChem value
pass as if it were a CompTox one.

## What Changes

- Add a PubChem client that finds a compound's CID (from a CAS number, and also from a SMILES
  or a name) and fetches its PUG View record. A SMILES is validated and canonicalized with
  RDKit first; a malformed one raises a descriptive `ValueError`.
- Make `fetch_chemical_properties` ask PubChem only for fields still null after CompTox, only
  those listed in configuration. Today: molecular weight, vapor pressure and density. A value
  from PubChem is converted and validated exactly like a CompTox value and is labelled
  `PubChem` in `sources`, with a warning that says it is a fallback. The tool description is
  not changed.
- Verify before using anything: the PubChem record must list the requested CAS number among
  its own CAS identifiers, otherwise nothing is taken from it (a name search can match another
  chemical).
- Fail closed: a PubChem value is used only when it states one number with a unit that converts
  to the target unit; conflicting statements are not averaged or guessed.
- Call PubChem politely and cheaply: at most 5 requests a second, a `User-Agent`, timeouts,
  and an on-disk SQLite cache of successful and "not found" answers.
- Configuration lists *what PubChem is asked for*: one `[[pubchem.fields]]` entry per field
  (key, PUG View heading, target unit), so another field (for example a reference dose, if a
  reliable PubChem source is found) is a config entry, not a code change. RfD, RfC, SF and IUR
  are **not** listed now: PubChem has no structured value for them.
- URL templates, headings, request policy and cache settings live in `config/settings.toml`.

Out of scope now (decided with the user): GHS classification and LC50/LD50 parsing (nothing in
the tool output carries them today), a PubChem preferred name (the name stays CompTox-only so
the agent never calls a chemical by an unverified name), and a separate agent tool.

Assumptions (flag in review if wrong):

- Location: `tools/informatics/helpers/pubchem/`, not `tools/chemicals/`, because `tools/` is
  grouped by concern and this is a helper of `fetch_chemical_properties`.
- Synchronous, reusing `tools/http.py` `RetryingClient`; results are typed, failures are
  `None` plus a reason.
- PubChem runs even when CompTox does not know the CAS number (the CAS check above guards the
  match); the name is still `None` in that case.
- The tool still needs the CompTox key: a missing key stays a setup error and PubChem is not
  used to hide it.

## Capabilities

### New Capabilities

- `pubchem-compound-resolution`: resolve a CAS number, SMILES or name to a PubChem CID and
  fetch the compound record, with RDKit validation of SMILES and CAS verification of the match.
- `pubchem-property-extraction`: read the configured fields from a PubChem record as values
  with units, rejecting statements that are not clear.
- `pubchem-request-policy`: rate limit, user agent, timeouts, retries and response cache.

### Modified Capabilities

- `chemical-properties-tool`: CompTox is no longer the only data service; PubChem fills
  missing configured fields, with its own provenance and warnings; the unresolvable-CAS case
  and the provenance rule change accordingly.

## Impact

- New code: `tools/informatics/helpers/pubchem/`, `config/pubchem.py`, `[pubchem]` in
  `config/settings.toml`, unit aliases for PubChem spellings (for example `g/cu cm`).
- Changed code: `tools/informatics/properties.py` (fallback step, default services) and
  `tools/schemas.py` (`sources` may say `PubChem`). The tool's model-facing description is
  deliberately unchanged (see design: evaluation finding).
- Tests: new ones under `tests/tools/informatics/helpers/pubchem/` and `tests/config/`;
  updated `test_properties`; a live smoke test; agent evals re-run to confirm no behavior
  change.
- No new dependencies. No change to the frontend or API contract beyond a new `sources` value.
