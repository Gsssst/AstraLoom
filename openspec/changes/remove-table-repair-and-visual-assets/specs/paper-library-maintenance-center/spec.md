## MODIFIED Requirements

### Requirement: Maintenance Center Supports Repair Actions
The maintenance center SHALL surface prioritized repair actions and let administrators run bounded retrieval maintenance jobs.

#### Scenario: Recommendations are available
- **WHEN** maintenance recommendations are returned
- **THEN** the page shows severity, reason, sample papers, and the action button for each recommendation.

#### Scenario: Admin runs a repair action
- **WHEN** the admin triggers BM25 rebuild, embedding backfill, or full-text backfill
- **THEN** the page calls the corresponding maintenance endpoint and refreshes health after completion.
