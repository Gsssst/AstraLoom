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

#### Scenario: Vector readiness is not blocked by visual OCR
- **WHEN** a paper is missing both vector embedding and visual evidence
- **THEN** automatic processing attempts vector generation before starting visual evidence OCR.

#### Scenario: BM25 readiness is process independent
- **WHEN** the paper database has a buildable BM25 corpus but the current web process has not warmed its local cache
- **THEN** processing status does not require a manual BM25 refresh solely because another process owns the warm cache.
