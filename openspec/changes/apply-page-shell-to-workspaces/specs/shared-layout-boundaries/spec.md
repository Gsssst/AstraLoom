## ADDED Requirements

### Requirement: Workspace List Uses Shared Page Shell

The Workspaces list page SHALL use the shared page shell for page-level title, subtitle, icon, and primary action placement.

#### Scenario: User opens project spaces
- **WHEN** the Workspaces page renders
- **THEN** it uses the shared page shell with a project-space title and subtitle
- **AND** the new-space action is rendered as a page shell action.

#### Scenario: User creates a project space
- **WHEN** the user clicks the shell-level new-space action
- **THEN** the existing create-space modal opens with the same form and submit behavior.
