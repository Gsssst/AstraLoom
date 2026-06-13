## MODIFIED Requirements

### Requirement: Paper Library Exposes Processing Readiness
The paper library SHALL show compact processing readiness labels for normal users and SHALL not require the maintenance center for routine artifact completion.

#### Scenario: User opens paper library
- **WHEN** a user opens the paper library
- **THEN** the page shows paper-level readiness labels for full text, structured parse, visual evidence/OCR, embeddings, and search index state when available
- **AND** it does not present manual maintenance as the primary way to make new papers usable.

#### Scenario: Admin opens maintenance center
- **WHEN** an administrator opens the maintenance center
- **THEN** the page presents diagnostics and fallback repair actions
- **AND** it explains or implies that normal processing is handled automatically in the background.

### Requirement: Maintenance Center Supports Repair Actions
The maintenance center SHALL keep bounded manual repair actions for administrators as a diagnostic fallback.

#### Scenario: Admin runs a repair action
- **WHEN** the admin triggers BM25 rebuild, embedding backfill, full-text backfill, structured PDF parse backfill, or visual evidence backfill
- **THEN** the page calls the corresponding maintenance endpoint and refreshes health after completion
- **AND** the action remains optional for recovery rather than required for newly ingested papers.
