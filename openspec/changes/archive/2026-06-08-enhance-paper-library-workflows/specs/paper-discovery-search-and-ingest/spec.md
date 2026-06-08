## ADDED Requirements

### Requirement: Paper library supports richer local filters
The paper library SHALL allow local papers to be filtered by importer, full-text availability, embedding availability, source, year, and current-user reading state.

#### Scenario: User filters by processing readiness
- **WHEN** a user selects full-text or embedding availability filters in the paper library
- **THEN** the local paper search returns only papers matching those readiness filters.

#### Scenario: User filters by importer
- **WHEN** a user selects an importer account filter
- **THEN** the local paper search returns papers imported by that account.

#### Scenario: User filters by reading state
- **WHEN** an authenticated user selects a reading-state filter
- **THEN** the local paper search returns papers with that user's selected reading state.

### Requirement: Paper search exposes processing readiness metadata
The paper search response SHALL include derived processing readiness fields for local papers.

#### Scenario: User views local paper cards
- **WHEN** local paper results are returned
- **THEN** each result includes whether PDF, full text, embeddings, and tags are available.
