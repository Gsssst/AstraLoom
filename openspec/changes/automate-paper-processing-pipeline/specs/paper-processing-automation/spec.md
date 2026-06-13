## ADDED Requirements

### Requirement: Automatic Paper Processing Lifecycle
The system SHALL automatically reconcile required paper-library processing artifacts after a paper is added or updated.

#### Scenario: Paper is ingested
- **WHEN** a paper is saved into the local paper library
- **THEN** the system enqueues background processing for that paper
- **AND** the processing lifecycle includes full text, structured PDF parse, visual evidence/OCR, embeddings, and search index readiness.

#### Scenario: Processing resumes later
- **WHEN** a paper has one or more missing, failed, or stale processing artifacts
- **THEN** a periodic background reconciler detects the incomplete state
- **AND** it schedules bounded work to complete the missing artifacts without requiring a user maintenance click.

### Requirement: Idempotent and Bounded Processing
The automatic processor SHALL avoid unnecessary reprocessing and SHALL bound expensive work.

#### Scenario: Paper artifacts are already ready
- **WHEN** the reconciler evaluates a paper whose artifacts are ready
- **THEN** it records no new processing work for that paper
- **AND** it does not rerun OCR, embedding generation, or structured parsing.

#### Scenario: Expensive work is needed
- **WHEN** visual OCR, embedding generation, or a search-index rebuild is needed
- **THEN** the reconciler runs within configured per-run limits
- **AND** remaining work is left for a later background run.

### Requirement: Processing Readiness Labels
The system SHALL expose compact readiness labels for paper-library processing state.

#### Scenario: User views the paper library
- **WHEN** a user opens the paper library or a paper detail page
- **THEN** each paper can show status labels for full text, structured parse, visual evidence/OCR, embedding, and search index readiness
- **AND** the user does not need to open a maintenance center to understand which artifacts are ready.

#### Scenario: Processing is still running
- **WHEN** at least one artifact is queued or running
- **THEN** the labels indicate pending/in-progress state without reporting a false success or false failure.
