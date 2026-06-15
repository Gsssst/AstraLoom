## MODIFIED Requirements

### Requirement: Workspace detail exposes role-aware quick starts

The frontend SHALL expose role-aware launchpad actions and a cockpit entry that connects evidence, ideas, writing, and issues on workspace detail.

#### Scenario: Editor opens workspace detail

- **WHEN** a user with owner or editor role opens a workspace
- **THEN** the page shows quick starts for binding papers, creating or binding research directions, opening writing work, and diagnosing the workspace through the AI assistant

#### Scenario: Viewer opens workspace detail

- **WHEN** a user with viewer role opens a workspace
- **THEN** the page shows read-oriented actions and cockpit status
- **AND** it does not expose resource-binding controls
