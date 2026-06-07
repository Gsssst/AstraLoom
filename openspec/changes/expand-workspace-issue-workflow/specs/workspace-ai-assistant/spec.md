## MODIFIED Requirements

### Requirement: Workspace assistant grounds responses in space context
The system SHALL ground workspace assistant replies in the project space's linked resources, open feedback issues, dashboard state, next actions, and recent activities.

#### Scenario: Assistant builds workspace context
- **GIVEN** a project space has linked papers, research projects, writing drafts, open feedback issues, dashboard state, and activities
- **WHEN** a user sends a workspace assistant message
- **THEN** the LLM prompt includes a concise workspace context assembled from those resources and issues
- **AND** the assistant is instructed to state when the provided context is insufficient

#### Scenario: Workspace has sparse resources
- **GIVEN** a project space has few or no linked resources
- **WHEN** a user sends a workspace assistant message
- **THEN** the assistant can still answer using dashboard, open issue, and next-action context
- **AND** the response explains which workspace resources should be added next when relevant

### Requirement: Workspace assistant returns resource references
The system SHALL return lightweight references for workspace resources and open feedback issues included in assistant context.

#### Scenario: Assistant references workspace resources
- **WHEN** a workspace assistant response uses linked papers, research projects, writing drafts, feedback issues, or activity context
- **THEN** the response includes references containing resource type, title, path, and source label
