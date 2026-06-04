# workspace-resource-access-control Specification

## ADDED Requirements

### Requirement: Workspace members can read linked research and writing resources

The system SHALL allow workspace members to read linked research projects and writing projects.

#### Scenario: Viewer opens linked writing project

- **GIVEN** a writing project is linked to a workspace
- **AND** a user is a workspace viewer
- **WHEN** the user opens the writing project
- **THEN** the project is returned

### Requirement: Workspace editors can update linked research and writing resources

The system SHALL allow workspace owners and editors to update linked research projects and writing projects.

#### Scenario: Editor updates linked writing section

- **GIVEN** a writing project is linked to a workspace
- **AND** a user is a workspace editor
- **WHEN** the user updates a section
- **THEN** the update succeeds

### Requirement: Workspace viewers cannot update linked resources

The system SHALL reject write attempts from workspace viewers.

#### Scenario: Viewer updates linked research project

- **GIVEN** a research project is linked to a workspace
- **AND** a user is a workspace viewer
- **WHEN** the user attempts to mutate the project
- **THEN** the request is rejected

### Requirement: Resource deletion remains owner-only

The system SHALL keep linked resource deletion restricted to the original resource owner.

#### Scenario: Workspace editor deletes linked writing project

- **GIVEN** a writing project is linked to a workspace
- **AND** a non-owner workspace editor tries to delete it
- **THEN** the request is rejected
