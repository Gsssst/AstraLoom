# paper-discovery-search-and-ingest Specification

## Purpose
TBD - created by archiving change paper-discovery-search-and-ingest. Update Purpose after archive.
## Requirements
### Requirement: Bounded resilient scholarly discovery
The system SHALL perform remote scholarly discovery without blocking the async server on a synchronous arXiv request, SHALL bound arXiv wait time, and SHALL fall back to configured public scholarly providers when an upstream source is unavailable.

#### Scenario: arXiv is slow
- **WHEN** a user searches arXiv for `video grounding` and the arXiv provider exceeds its bounded wait time
- **THEN** the system returns matching fallback scholarly previews or a controlled empty response without blocking other backend requests indefinitely

#### Scenario: fallback provider is visible
- **WHEN** a remote preview was discovered through a fallback provider
- **THEN** the preview identifies the actual provider used for that result

### Requirement: Multi-provider de-duplication
The system SHALL merge scholarly candidates using stable identifiers and normalized titles so the same paper is not shown repeatedly.

#### Scenario: duplicate DOI from two providers
- **WHEN** two provider results have the same DOI
- **THEN** the system returns one preview card for that paper

### Requirement: Authenticated personal paper ingestion
The system SHALL allow an authenticated user to add a single remote preview to their personal paper library through a server-resolved identifier while preserving administrator-only bulk ingestion.

#### Scenario: regular user adds an OpenAlex preview
- **WHEN** a logged-in non-admin user clicks “加入论文库” on an OpenAlex preview
- **THEN** the server resolves the OpenAlex work, stores or reuses the paper record, and marks it saved for that user
- **AND** newly stored paper records identify the importing account.

#### Scenario: unauthenticated user views remote results
- **WHEN** an unauthenticated user views a remote preview
- **THEN** the interface does not offer an active personal-ingestion action

#### Scenario: bulk ingestion permissions remain restricted
- **WHEN** a non-admin user calls the administrator bulk-ingestion endpoint
- **THEN** the server rejects the request

### Requirement: Paper library exposes importer ownership
The paper library SHALL expose the account that originally imported each local paper.

#### Scenario: User views local paper results
- **WHEN** the paper library renders local paper cards
- **THEN** each paper with importer metadata shows an account tag for that importer.

#### Scenario: Historical papers are migrated
- **WHEN** existing paper rows are migrated to the new ownership metadata
- **THEN** they are labeled as imported by `gst`.

### Requirement: Paper library can filter to my imported papers
The paper library SHALL allow an authenticated user to view papers imported by their own account.

#### Scenario: User selects my paper filter
- **WHEN** an authenticated user selects the "我的" filter
- **THEN** the local paper search returns papers imported by that user.

#### Scenario: User changes away from my paper filter
- **WHEN** the user switches back to broader paper-library filters
- **THEN** the library returns the normal local/global paper results.

### Requirement: Clear remote discovery failures
The interface SHALL surface a useful remote-discovery error message when the backend reports an upstream failure.

#### Scenario: backend returns provider error detail
- **WHEN** remote discovery fails with an API error detail
- **THEN** the paper-library interface displays that detail instead of only a generic failure message

### Requirement: Paper Library Shows Persistent API Recovery
The paper library frontend SHALL show persistent structured recovery guidance for failed paper search, import, collection, reading status, maintenance, deletion, report, and export operations.

#### Scenario: Paper library action fails
- **WHEN** a paper library API action fails
- **THEN** the paper library displays a structured recovery alert derived from the shared API error helper
- **AND** the user can dismiss the alert and keep current page state.

#### Scenario: Paper library action succeeds after a previous failure
- **WHEN** a paper library API action succeeds after an earlier failure
- **THEN** stale paper-library recovery guidance is cleared when the successful action makes it obsolete.

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
