# stack-parameters-scc-fallback Specification

## Purpose

Tier 2 source of stack parameters for facilities the NEI does not cover: SCC-keyed defaults from EPA PSTK (Point Source Stack Replacements), ending in the AirToxScreen global point-source default so the agent always gets a usable, clearly labelled value set.

## Requirements


### Requirement: PSTK stack defaults by SCC
The system SHALL provide a tool that, given a Source Classification Code, returns stack height (m), stack diameter (m), exit velocity (m/s) and exit temperature (K) from a bundled PSTK file, converted from the units the file reports. The result SHALL identify PSTK as its source and SHALL include the SCC that matched. The tool SHALL NOT call a network service.

#### Scenario: SCC present
- **WHEN** the tool is called with an SCC that has a complete, plausible row in the PSTK file
- **THEN** it returns the four converted values with source "PSTK" and the matched SCC

#### Scenario: SCC formatting
- **WHEN** the SCC is given with surrounding whitespace, or as an integer
- **THEN** the lookup matches the same row as the canonical digit string, and the result's SCC is that matched code

#### Scenario: SCC must match exactly
- **WHEN** the SCC differs from every PSTK code, including by an extra leading zero, or is the file's all-zero default row
- **THEN** it returns the global default with a warning that the SCC was not found

### Requirement: Global point-source fallback
When no SCC is given (the input is null or omitted), or the SCC is absent from the PSTK file, malformed, or its PSTK row has any missing or implausible value, the system SHALL return the AirToxScreen global point-source default: stack height 3.0 m, stack diameter 0.2 m, exit velocity 4.0 m/s, exit temperature 295.4 K. The result SHALL identify the source as the global default and SHALL include a warning explaining why PSTK was not used. Fallback values SHALL come from configuration, not code.

#### Scenario: SCC not in PSTK
- **WHEN** the SCC is valid but has no PSTK row
- **THEN** it returns 3.0 m, 0.2 m, 4.0 m/s and 295.4 K with source "AirToxScreen global default" and a warning that the SCC was not found

#### Scenario: No SCC given
- **WHEN** the tool is called with a null SCC or without one
- **THEN** it returns the global default with a warning that no SCC was given, and the PSTK file is not searched

#### Scenario: Malformed SCC
- **WHEN** the SCC is empty or contains non-digit characters
- **THEN** it returns the global default with a warning that the SCC is invalid, and the PSTK file is not searched

#### Scenario: Implausible PSTK row
- **WHEN** the PSTK row for the SCC has a non-finite, non-positive or out-of-range value
- **THEN** it returns the global default with a warning naming the bad field; PSTK and default values are never mixed

### Requirement: Tool description states when to use tier 2
The tool's description, as seen by the LLM, SHALL state that it is to be used only after the NEI tool returned no values for the facility, that the values are generic defaults for the process type rather than facility measurements, and that the result may be the global default.

#### Scenario: Description content
- **WHEN** the tool's description is read
- **THEN** it contains the use-only-after-NEI instruction, names the SCC input, gives units for each output, and explains the `source` field values
