## MODIFIED Requirements

### Requirement: Command palette searches lightweight resources
The command palette SHALL search lightweight existing resources and workspace issues without requiring a new standalone search service.

#### Scenario: Authenticated user searches resources
- **WHEN** an authenticated user enters a non-empty query
- **THEN** the palette requests lightweight results from existing paper, research, workspace, writing, and workspace issue data where available
- **AND** matching resource and issue commands appear alongside static commands

#### Scenario: Resource search fails
- **WHEN** one or more resource search requests fail
- **THEN** the palette keeps static commands usable
- **AND** it shows a compact resource search unavailable state instead of blocking the whole palette

#### Scenario: User selects a resource result
- **WHEN** a user selects a paper, research project, workspace, workspace issue, or writing result
- **THEN** the palette closes and the app navigates to that resource or its best existing workflow route
