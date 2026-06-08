## MODIFIED Requirements

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: Warning details are collapsed by default
- **WHEN** LaTeX compilation succeeds or fails with warning diagnostics
- **THEN** the UI shows the warning count
- **AND** keeps the warning details available behind a collapsed control
- **AND** does not expand warning details by default.

#### Scenario: Error details remain visible
- **WHEN** LaTeX compilation returns errors
- **THEN** the UI shows error details directly without requiring expansion.
