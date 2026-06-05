## ADDED Requirements

### Requirement: Full abstract inspection
The paper-library interface SHALL allow a user to open a result-card detail view that displays the complete available abstract and core metadata without requiring ingestion.

#### Scenario: Remote result has an abstract
- **WHEN** a user clicks “查看摘要” on a remote result card
- **THEN** the interface opens a modal containing the full available abstract, title, authors, publication year, and source

#### Scenario: Result has no abstract
- **WHEN** a user opens the abstract detail view for a result without an abstract
- **THEN** the interface displays a clear empty-abstract message

### Requirement: Different remote result batches
The system SHALL support deterministic remote result paging and SHALL expose a “换一批” action that requests the next provider offset.

#### Scenario: User requests another batch
- **WHEN** a user clicks “换一批” after an arXiv search
- **THEN** the interface requests the next remote page while preserving query and year filters

#### Scenario: User starts a new search
- **WHEN** a user changes search conditions and submits a new search
- **THEN** the interface resets remote discovery to the first batch

### Requirement: Publication-year filtering
The paper-library interface SHALL allow a user to select optional start and end publication years for local and remote searches.

#### Scenario: Valid range
- **WHEN** a user searches with start year 2022 and end year 2026
- **THEN** the request includes `year_from=2022` and `year_to=2026`

#### Scenario: Invalid range
- **WHEN** a user selects a start year greater than the end year
- **THEN** the interface rejects the search and explains the invalid range

