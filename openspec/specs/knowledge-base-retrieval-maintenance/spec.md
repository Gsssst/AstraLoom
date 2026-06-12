# knowledge-base-retrieval-maintenance Specification

## Purpose
TBD - created by archiving change knowledge-base-retrieval-maintenance. Update Purpose after archive.
## Requirements
### Requirement: Retrieval Health Visibility

Administrators SHALL be able to inspect paper-library retrieval health from an API endpoint and the settings UI.

#### Scenario: Admin views retrieval health

- **GIVEN** an authenticated administrator
- **WHEN** they open the knowledge-base maintenance console
- **THEN** the system displays total papers, full-text coverage, embedding coverage, and BM25 index state
- **AND** it lists small samples of papers missing full text or embeddings.

### Requirement: Bounded Retrieval Maintenance Actions

Administrators SHALL be able to rebuild BM25 and backfill missing retrieval artifacts in bounded batches.

#### Scenario: Admin repairs retrieval state

- **GIVEN** an authenticated administrator
- **WHEN** they trigger BM25 rebuild, embedding backfill, or full-text backfill
- **THEN** the operation runs with a bounded limit where applicable
- **AND** returns processed, success, failed, and skipped counts
- **AND** the UI refreshes the health summary after the operation.

### Requirement: Search Diagnostics

Administrators SHALL be able to diagnose a local search query by comparing BM25, dense, and hybrid retrieval outputs.

#### Scenario: Admin diagnoses a query

- **GIVEN** an authenticated administrator and a query
- **WHEN** they run diagnostics
- **THEN** the system returns result lists for BM25, dense, and hybrid retrieval
- **AND** each result includes title, score, year, source, and flags for full text and embedding availability.

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

### Requirement: Visual Evidence Maintenance Visibility
Administrators SHALL be able to inspect whether papers have visual assets and visual summaries available for multimodal Q&A.

#### Scenario: Admin views visual evidence maintenance health
- **WHEN** an administrator opens the knowledge-base maintenance console
- **THEN** the system displays counts or recommendations for papers missing visual assets and papers missing visual summaries.

### Requirement: Bounded Visual Evidence Maintenance Actions
Administrators SHALL be able to extract visual assets and summarize visual evidence in bounded batches.

#### Scenario: Admin backfills visual evidence
- **WHEN** an administrator triggers visual asset extraction or visual summary backfill
- **THEN** the operation runs with a bounded limit
- **AND** returns processed, success, failed, skipped counts, and actionable errors.
