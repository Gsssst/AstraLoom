## ADDED Requirements

### Requirement: Search results expose import-readiness state
The paper-library interface SHALL derive and display a clear action state for each visible search result.

#### Scenario: Remote result can be imported
- **WHEN** a remote search result has a stable remote identifier and is not already imported in the current session
- **THEN** the result is labeled as importable
- **AND** the personal-ingestion action remains available for authenticated users

#### Scenario: Remote result lacks identifier
- **WHEN** a remote search result lacks the stable remote identifier required for personal ingestion
- **THEN** the result is labeled as missing a remote ID
- **AND** the interface does not present an active personal-ingestion action for that result

#### Scenario: Local result is already in library
- **WHEN** a search result has a local paper identifier
- **THEN** the result is labeled as already in the library

### Requirement: Search results can be filtered by action state
The paper-library interface SHALL allow users to filter the current result set by derived action state without changing the active provider search.

#### Scenario: Filter importable remote results
- **WHEN** a user selects the importable filter
- **THEN** only remote results that can currently be imported are shown

#### Scenario: Filter has no matching results
- **WHEN** the active action-state filter matches no current results
- **THEN** the interface shows an empty state explaining that no results match the current status filter
- **AND** the user can return to all result states

### Requirement: Post-import feedback updates the result state
The paper-library interface SHALL immediately reflect successful single-paper imports in the current result list.

#### Scenario: Remote result imported successfully
- **WHEN** a user successfully adds a remote result to the personal paper library
- **THEN** the result is marked as imported in the current result set
- **AND** status summary counts update without requiring a full page refresh

### Requirement: Result state summary is visible
The paper-library interface SHALL show a compact summary of current result states.

#### Scenario: Mixed local and remote results
- **WHEN** current results include local, importable remote, imported, open-PDF, and missing-ID results
- **THEN** the paper list header shows counts for those states
