## MODIFIED Requirements

### Requirement: Paper records expose core metadata
The paper API SHALL expose paper identity, bibliographic metadata, source metadata, processing state, import ownership, and shared importance marker metadata.

#### Scenario: Paper has a shared importance marker
- **WHEN** a paper response is serialized
- **AND** the paper has an importance label and note
- **THEN** the response includes `importance_label` and `importance_note`

#### Scenario: Paper has no shared importance marker
- **WHEN** a paper response is serialized
- **AND** the paper has no importance label
- **THEN** the response includes a null or absent marker value that the frontend treats as unmarked

### Requirement: Authenticated users can update shared paper importance
The paper API SHALL allow authenticated users to set or clear a shared importance marker on a library paper.

#### Scenario: User marks a paper as important
- **WHEN** an authenticated user sets a paper marker to `important`
- **THEN** the paper stores the marker
- **AND** subsequent paper responses expose the marker to all users

#### Scenario: User marks a paper as interesting
- **WHEN** an authenticated user sets a paper marker to `interesting`
- **THEN** the paper stores the marker
- **AND** subsequent paper responses expose the marker to all users

#### Scenario: User clears the marker
- **WHEN** an authenticated user sets the paper marker label to null
- **THEN** the paper clears the marker label and note

#### Scenario: User submits an invalid marker
- **WHEN** an authenticated user submits a marker label outside the supported values
- **THEN** the API rejects the request with validation feedback
