## MODIFIED Requirements

### Requirement: Automatic Paper Artifact Processing
The system SHALL automatically process imported papers through the background paper artifact lifecycle and expose compact artifact readiness labels.

#### Scenario: Background visual evidence reconciliation succeeds
- **WHEN** automatic reconciliation reprocesses a paper whose visual evidence contains parser candidates corrected by OCR to non-table evidence
- **THEN** the visual evidence step uses the same readiness criteria as manual single-paper extraction
- **AND** it does not mark the paper failed only because corrected non-table candidates lack markdown table OCR.

#### Scenario: Background retry recovers old visual asset failures
- **WHEN** automatic reconciliation reprocesses a paper with stale visual asset errors from a previously missing renderer dependency
- **THEN** a successful forced visual extraction replaces the stale failure metadata
- **AND** the visual evidence label no longer reports the old asset error.
