## MODIFIED Requirements

### Requirement: Retrieval Health Visibility

Administrators SHALL be able to inspect paper-library retrieval health from an API endpoint and the settings UI.

#### Scenario: Admin views retrieval health

- **GIVEN** an authenticated administrator
- **WHEN** they open the knowledge-base maintenance console
- **THEN** the system displays total papers, full-text coverage, embedding coverage, BM25 index state, and document visual evidence readiness
- **AND** it lists small samples of papers missing full text, embeddings, or ready visual/table evidence.

### Requirement: Bounded Retrieval Maintenance Actions

Administrators SHALL be able to rebuild BM25 and backfill missing retrieval artifacts in bounded batches.

#### Scenario: Admin repairs retrieval state

- **GIVEN** an authenticated administrator
- **WHEN** they trigger BM25 rebuild, embedding backfill, full-text backfill, or visual evidence backfill
- **THEN** the operation runs with a bounded limit where applicable
- **AND** returns processed, success, failed, and skipped counts
- **AND** the UI refreshes the health summary after the operation.

### Requirement: Search Diagnostics

Administrators SHALL be able to diagnose a local search query by comparing BM25, dense, hybrid, and document visual evidence retrieval outputs when visual evidence is available.

#### Scenario: Admin diagnoses a query

- **GIVEN** an authenticated administrator and a query
- **WHEN** they run diagnostics
- **THEN** the system returns result lists for BM25, dense, hybrid, and visual evidence branches where applicable
- **AND** each paper result includes title, score, year, source, and flags for full text, embedding, and visual evidence availability.

### Requirement: Maintenance Authorization and Route Safety

Maintenance endpoints SHALL be fixed routes and SHALL require administrator authorization.

#### Scenario: Maintenance path is not treated as a paper id

- **GIVEN** the paper API contains dynamic paper detail routes
- **WHEN** `/api/papers/maintenance/health` is registered
- **THEN** it appears before `/api/papers/{paper_id}`
- **AND** it requires administrator authorization.

### Requirement: Maintenance actions tolerate long-running operations

Knowledge-base maintenance UI actions SHALL use a longer client timeout than normal API calls for operations that can download/load models or process multiple papers.

#### Scenario: Admin backfills embeddings on a fresh server

- **WHEN** an admin starts embedding backfill from the maintenance UI
- **AND** the server needs extra time to load or download the embedding model
- **THEN** the frontend keeps waiting beyond the default 30-second API timeout
- **AND** it reports the backend maintenance result when the request completes

#### Scenario: Admin backfills visual evidence on a fresh server
- **WHEN** an admin starts visual evidence backfill and the server needs extra time to load an optional parser or call a configured vision provider
- **THEN** the frontend keeps waiting or polls the job status according to the maintenance action type
- **AND** it reports processed, success, failed, skipped, and actionable parser/model errors.

### Requirement: Visual Evidence Maintenance Visibility
Administrators SHALL be able to inspect whether papers have ready document visual evidence, visual assets, visual OCR/summaries, and visual table evidence available for multimodal Q&A.

#### Scenario: Admin views visual evidence maintenance health
- **WHEN** an administrator opens the knowledge-base maintenance console
- **THEN** the system displays counts or recommendations for papers missing visual evidence, papers with failed visual extraction, papers missing visual summaries/OCR, and papers whose table evidence is low confidence.

### Requirement: Bounded Visual Evidence Maintenance Actions
Administrators SHALL be able to extract visual evidence and summarize or OCR selected visual crops in bounded batches.

#### Scenario: Admin backfills visual evidence
- **WHEN** an administrator triggers visual asset extraction or visual summary/OCR backfill
- **THEN** the operation runs with a bounded limit
- **AND** returns processed, success, failed, skipped counts, and actionable errors.

#### Scenario: Admin retries failed visual extraction
- **WHEN** a paper has a recorded visual extraction failure
- **THEN** the maintenance action can retry that paper without requiring unrelated full-text or embedding repair.
