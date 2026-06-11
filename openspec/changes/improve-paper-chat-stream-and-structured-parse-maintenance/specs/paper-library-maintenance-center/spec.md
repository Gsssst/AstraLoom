## ADDED Requirements

### Requirement: Maintenance Center Supports Structured PDF Parse Repair
The maintenance center SHALL let administrators run bounded structured PDF parsing maintenance for papers with available PDFs or arXiv IDs and SHALL show structured parse readiness in processing status.

#### Scenario: Admin opens maintenance center
- **WHEN** an administrator opens the paper library maintenance center
- **THEN** the page shows structured PDF parse readiness for listed papers when status data is available
- **AND** provides a bounded action to parse or refresh structured PDF metadata

#### Scenario: Admin runs structured PDF parse maintenance
- **WHEN** the admin triggers structured PDF parse maintenance
- **THEN** the backend reparses a bounded set of eligible papers
- **AND** returns processed, success, failed, skipped, and per-paper error counts
- **AND** the frontend refreshes maintenance status after completion

#### Scenario: Non-admin views maintenance center
- **WHEN** a non-admin opens the maintenance view
- **THEN** structured PDF parse repair actions are not exposed
