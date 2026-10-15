## REMOVED Requirements

### Requirement: Resolve CAS number to canonical SMILES
**Reason**: CompTox is now queried by CAS number directly, and its CAS search returns the structure used for molecular weight, so a separate PubChem lookup is unused.
**Migration**: None needed; callers use the CompTox helper (structure via its CAS lookup).

### Requirement: Fall back across PubChem SMILES fields
**Reason**: CompTox is now queried by CAS number directly, and its CAS search returns the structure used for molecular weight, so a separate PubChem lookup is unused.
**Migration**: None needed; callers use the CompTox helper (structure via its CAS lookup).

### Requirement: Tolerate service failures
**Reason**: CompTox is now queried by CAS number directly, and its CAS search returns the structure used for molecular weight, so a separate PubChem lookup is unused.
**Migration**: None needed; callers use the CompTox helper (structure via its CAS lookup).

### Requirement: Cache lookups
**Reason**: CompTox is now queried by CAS number directly, and its CAS search returns the structure used for molecular weight, so a separate PubChem lookup is unused.
**Migration**: None needed; callers use the CompTox helper (structure via its CAS lookup).

### Requirement: Respect PubChem rate limits
**Reason**: CompTox is now queried by CAS number directly, and its CAS search returns the structure used for molecular weight, so a separate PubChem lookup is unused.
**Migration**: None needed; callers use the CompTox helper (structure via its CAS lookup).
