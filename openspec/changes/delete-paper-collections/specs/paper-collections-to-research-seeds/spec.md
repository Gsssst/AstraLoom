# Capability: Paper Collections To Research Seeds

## MODIFIED Requirements

### Requirement: Users can manage personal paper collections

Authenticated users SHALL be able to create, delete, and organize named paper collections, and manage the papers inside them.

#### Scenario: User creates a collection

- **GIVEN** an authenticated user
- **WHEN** they create a paper collection with a name
- **THEN** the collection is owned by that user
- **AND** it appears in their collection list

#### Scenario: User deletes a collection

- **GIVEN** an authenticated user owns a paper collection
- **WHEN** they confirm deletion of that collection
- **THEN** the collection no longer appears in their collection list
- **AND** papers that were in the collection remain in the user's paper library

#### Scenario: User deletes the currently selected collection

- **GIVEN** the user is viewing a selected paper collection
- **WHEN** they delete that collection
- **THEN** the paper library clears the deleted collection's diagnostics and visible paper list
- **AND** it selects another collection when one remains

#### Scenario: User adds papers to a collection

- **GIVEN** a user owns a collection
- **WHEN** they add one or more paper IDs to it
- **THEN** the papers are associated with that collection
- **AND** the user's personal saved state for those papers is preserved or created

#### Scenario: User lists collection papers

- **GIVEN** a user owns a collection with papers
- **WHEN** they open the collection
- **THEN** only papers from that collection are returned
