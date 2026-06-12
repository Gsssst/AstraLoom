## ADDED Requirements

### Requirement: Structured table repair degrades gracefully
The paper AI backend SHALL keep structured paper extraction usable when high-fidelity table repair cannot run.

#### Scenario: High-fidelity table parser fails
- **WHEN** the configured high-fidelity table parser exits non-zero, times out, or is killed
- **THEN** the backend preserves the existing structured extraction result
- **AND** records repair metadata that identifies the failure class.

#### Scenario: Lightweight fallback extracts tables
- **WHEN** a lightweight table extraction fallback returns usable table rows for a low-quality table paper
- **THEN** the backend merges the fallback table blocks into the structured extraction
- **AND** marks the repaired blocks with parser and quality metadata.
