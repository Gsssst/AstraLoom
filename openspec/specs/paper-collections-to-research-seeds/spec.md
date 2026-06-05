# paper-collections-to-research-seeds Specification

## Purpose
TBD - created by archiving change paper-collections-to-research-seeds. Update Purpose after archive.
## Requirements
### Requirement: Users can manage personal paper collections

Authenticated users SHALL be able to create named paper collections and manage the papers inside them.

#### Scenario: User creates a collection

- **GIVEN** an authenticated user
- **WHEN** they create a paper collection with a name
- **THEN** the collection is owned by that user
- **AND** it appears in their collection list

#### Scenario: User adds papers to a collection

- **GIVEN** a user owns a collection
- **WHEN** they add one or more paper IDs to it
- **THEN** the papers are associated with that collection
- **AND** the user's personal saved state for those papers is preserved or created

#### Scenario: User lists collection papers

- **GIVEN** a user owns a collection with papers
- **WHEN** they open the collection
- **THEN** only papers from that collection are returned

### Requirement: Research directions can use collections as seed papers

The research direction creation flow SHALL allow users to select one or more paper collections and import their papers as seed papers.

#### Scenario: User creates a direction from a collection

- **GIVEN** a user has a collection containing papers
- **WHEN** they create a research direction and select that collection
- **THEN** all paper IDs from the collection are included in the created project's seed paper list
- **AND** manually selected papers are merged without duplicates

