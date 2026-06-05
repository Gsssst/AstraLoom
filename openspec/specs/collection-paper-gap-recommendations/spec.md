# collection-paper-gap-recommendations Specification

## Purpose
TBD - created by archiving change collection-paper-gap-recommendations. Update Purpose after archive.
## Requirements
### Requirement: Collection Coverage Analysis

The system SHALL expose deterministic topic coverage diagnostics for a user's paper collection.

#### Scenario: Collection has papers

- **WHEN** an authenticated user requests coverage for their collection
- **THEN** the response includes topic terms, topic statuses, matched counts, and recommended follow-up queries.

#### Scenario: Collection has weak or missing branches

- **WHEN** a topic has no matching paper or only thin evidence in the collection
- **THEN** the response marks that topic as missing or thin and includes a query that can be used to search for补充论文.

### Requirement: Collection Paper Recommendations

The system SHALL recommend external paper candidates for a collection by classic, recent, gap, or related recommendation kind.

#### Scenario: User asks for gap recommendations

- **WHEN** an authenticated user requests gap recommendations for a collection
- **THEN** the system searches scholarly providers using the first missing or thin coverage topic and returns normalized remote paper candidates with ingest tokens.

#### Scenario: Recommended candidate already exists in the collection

- **WHEN** a remote search result matches an existing collection paper by arXiv ID, DOI, remote ID, or normalized title
- **THEN** that candidate is excluded from the recommendation response.

### Requirement: Collection Recommendations Can Be Added In Place

The paper library SHALL let users ingest recommended candidates directly into the selected collection.

#### Scenario: User adds a recommended paper

- **WHEN** the user clicks the add button on a recommendation card
- **THEN** the system ingests the remote paper into the user's library and adds the resulting local paper to the selected collection.

