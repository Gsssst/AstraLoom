# workspace-resource-picker Specification

## Purpose
Define the searchable workspace resource picker that lets owners and editors attach papers, research projects, and writing drafts without leaving the workspace or copying raw resource ids.
## Requirements
### Requirement: Workspace exposes searchable resource candidates

The system SHALL expose a workspace-scoped candidate search endpoint for supported resource types.

#### Scenario: User searches papers

- **GIVEN** a workspace member
- **WHEN** they search paper candidates
- **THEN** matching local papers are returned with title, subtitle, path, and linked status

### Requirement: Workspace resource picker shows linked status

The frontend SHALL show whether candidate resources are already linked to the workspace.

#### Scenario: Resource already linked

- **GIVEN** a candidate resource is already bound to the workspace
- **WHEN** the picker renders the candidate
- **THEN** it is marked as already linked and cannot be bound again

### Requirement: Workspace resource picker supports one-click binding

The frontend SHALL allow owners and editors to bind a candidate resource without copying ids.

#### Scenario: Editor binds candidate

- **GIVEN** a workspace editor sees an unlinked candidate
- **WHEN** they click bind
- **THEN** the resource is linked and the workspace summary refreshes

### Requirement: Manual resource id fallback remains available

The frontend SHALL retain a manual id binding fallback.

#### Scenario: User has a resource id

- **GIVEN** a workspace owner or editor has a valid resource id
- **WHEN** they use the manual fallback
- **THEN** the existing resource link API is used
