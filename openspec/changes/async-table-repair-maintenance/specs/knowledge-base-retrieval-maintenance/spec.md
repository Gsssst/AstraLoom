## ADDED Requirements

### Requirement: Low-quality table repair runs as a tracked maintenance job

Administrators SHALL be able to start low-quality table repair as an asynchronous maintenance job and inspect the job status without keeping the initiating HTTP request open for the full Marker runtime.

#### Scenario: Admin starts table repair

- **WHEN** an authenticated administrator starts low-quality table repair from the maintenance center
- **THEN** the backend enqueues a bounded repair job
- **AND** returns a job id, initial status, and status endpoint immediately.

#### Scenario: Admin polls repair progress

- **WHEN** the maintenance UI polls the returned job status endpoint
- **THEN** the backend returns the current job state, processed count, success count, failure count, skipped count, total count when known, current paper when available, and accumulated errors.

#### Scenario: Repair job completes

- **WHEN** the queued table repair job reaches a terminal success or failure state
- **THEN** the UI displays the final counts or failure reason
- **AND** refreshes maintenance health, recommendations, and paper processing status.

#### Scenario: Marker runtime exceeds normal client timeout

- **WHEN** Marker takes longer than the normal API timeout to load models or repair a PDF
- **THEN** the maintenance UI SHALL continue showing the queued/running job state through polling
- **AND** SHALL NOT report the original start request as a completed maintenance failure solely because table repair is still running.
