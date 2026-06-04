# workspace-resource-backlinks Specification

## ADDED Requirements

### Requirement: Resource pages can query workspace link status

The system SHALL expose the current user's visible project spaces for a resource with linked status.

#### Scenario: User queries paper workspaces

- **GIVEN** the user belongs to project spaces
- **WHEN** they query workspace links for a paper
- **THEN** each visible space includes id, name, role, linked status, and edit capability

### Requirement: Resource pages can link resources to spaces

The frontend SHALL let owners and editors link the current resource to an available workspace.

#### Scenario: Editor links current paper

- **GIVEN** the user is an editor in a workspace
- **WHEN** they click add from the paper page
- **THEN** the paper is linked to that workspace

### Requirement: Resource pages can unlink resources from spaces

The frontend SHALL let owners and editors remove the current resource from linked spaces.

#### Scenario: Owner removes writing project from space

- **GIVEN** the current writing project is linked to a workspace
- **AND** the user can edit workspace resources
- **WHEN** they click remove
- **THEN** the writing project is unlinked from that workspace

### Requirement: Backlink component is available on key resource pages

The frontend SHALL show workspace backlinks on paper, research project, and writing project pages.

#### Scenario: User opens research project

- **GIVEN** the research project page has loaded
- **WHEN** the project id is known
- **THEN** workspace link controls are visible
