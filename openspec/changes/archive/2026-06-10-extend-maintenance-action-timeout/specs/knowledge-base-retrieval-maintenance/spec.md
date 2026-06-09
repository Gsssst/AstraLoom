## MODIFIED Requirements

### Requirement: Maintenance actions tolerate long-running operations
Knowledge-base maintenance UI actions SHALL use a longer client timeout than normal API calls for operations that can download/load models or process multiple papers.

#### Scenario: Admin backfills embeddings on a fresh server
- **WHEN** an admin starts embedding backfill from the maintenance UI
- **AND** the server needs extra time to load or download the embedding model
- **THEN** the frontend keeps waiting beyond the default 30-second API timeout
- **AND** it reports the backend maintenance result when the request completes
