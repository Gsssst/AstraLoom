## MODIFIED Requirements

### Requirement: Maintenance center shows paper processing status
The maintenance center SHALL show a bounded paper-processing status list for local papers.

#### Scenario: Admin opens processing status
- **WHEN** an administrator opens the maintenance view
- **THEN** the page shows papers with PDF, full-text, embedding, tag, structured parse, and visual evidence readiness indicators.

#### Scenario: Admin runs repair action from processing status
- **WHEN** a paper is missing full text, embedding, structured parse, or visual evidence
- **THEN** the maintenance center provides a bounded repair action using the corresponding backend endpoint.

#### Scenario: Non-admin opens processing status
- **WHEN** a non-admin opens the maintenance view
- **THEN** processing status is informational and privileged repair actions are hidden.

#### Scenario: Queued metadata does not block automatic processing
- **WHEN** a paper has queued processing metadata but no fresh running step
- **THEN** automatic reconciliation can select the paper and execute missing or failed artifact steps.

#### Scenario: Ready artifacts clear obsolete active metadata
- **WHEN** a paper has queued or running metadata for an artifact that is already ready
- **THEN** the system clears that artifact's obsolete active metadata and does not keep showing it as processing.
