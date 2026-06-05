## ADDED Requirements

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

#### Scenario: unauthenticated user views remote results
- **WHEN** an unauthenticated user views a remote preview
- **THEN** the interface does not offer an active personal-ingestion action

#### Scenario: bulk ingestion permissions remain restricted
- **WHEN** a non-admin user calls the administrator bulk-ingestion endpoint
- **THEN** the server rejects the request

### Requirement: Clear remote discovery failures
The interface SHALL surface a useful remote-discovery error message when the backend reports an upstream failure.

#### Scenario: backend returns provider error detail
- **WHEN** remote discovery fails with an API error detail
- **THEN** the paper-library interface displays that detail instead of only a generic failure message

