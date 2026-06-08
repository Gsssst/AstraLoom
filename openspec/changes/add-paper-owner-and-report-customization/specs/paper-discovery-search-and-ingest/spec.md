## MODIFIED Requirements

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

## ADDED Requirements

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
