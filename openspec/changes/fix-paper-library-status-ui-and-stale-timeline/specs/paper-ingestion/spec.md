## ADDED Requirements

### Requirement: Processing timeline ignores stale failures for ready steps
The paper processing timeline SHALL present the current readiness state of each step and SHALL NOT display stale failure errors for steps that are currently ready.

#### Scenario: Visual evidence is currently ready after previous failure
- **WHEN** a paper has historical `failed_steps.visual_evidence` metadata
- **AND** the current visual evidence label is ready
- **THEN** the processing timeline SHALL show the visual evidence step as ready
- **AND** it SHALL use ready detail/timestamps rather than the historical failure message.

#### Scenario: Step is still failed
- **WHEN** a processing step is currently failed
- **THEN** the processing timeline SHALL include the current failure message, failure timestamp, and retry hint when available.
