## MODIFIED Requirements

### Requirement: Maintenance Center Supports Repair Actions
The maintenance center SHALL surface prioritized repair actions and let administrators run bounded maintenance jobs, while keeping the top-level action row focused on current retrieval and visual-evidence maintenance paths.

#### Scenario: Recommendations are available
- **WHEN** maintenance recommendations are returned
- **THEN** the page shows severity, reason, sample papers, and the action button for each recommendation.

#### Scenario: Admin runs a repair action
- **WHEN** the admin triggers BM25 rebuild, embedding backfill, full-text backfill, or visual evidence backfill from the top-level maintenance action row
- **THEN** the page calls the corresponding maintenance endpoint and refreshes health after completion.

#### Scenario: Admin views top-level maintenance actions
- **WHEN** an administrator opens the maintenance center
- **THEN** the top-level action row exposes the current visual evidence extraction batch action
- **AND** the row does not expose structured PDF parse backfill as a peer primary batch action.
