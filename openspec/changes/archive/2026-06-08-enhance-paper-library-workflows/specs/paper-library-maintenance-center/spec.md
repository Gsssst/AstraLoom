## ADDED Requirements

### Requirement: Maintenance center shows paper processing status
The maintenance center SHALL show a bounded paper-processing status list for local papers.

#### Scenario: Admin opens processing status
- **WHEN** an administrator opens the maintenance view
- **THEN** the page shows papers with PDF, full-text, embedding, and tag readiness indicators.

#### Scenario: Admin runs repair action from processing status
- **WHEN** a paper is missing full text or embedding
- **THEN** the maintenance center provides a bounded repair action using existing full-text and embedding endpoints.

#### Scenario: Non-admin opens processing status
- **WHEN** a non-admin opens the maintenance view
- **THEN** processing status is informational and privileged repair actions are hidden.
