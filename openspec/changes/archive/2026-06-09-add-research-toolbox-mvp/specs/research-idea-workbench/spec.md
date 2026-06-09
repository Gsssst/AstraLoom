## MODIFIED Requirements

### Requirement: Project-owned staged idea run
The system SHALL create and execute a project-owned staged idea generation run that records status, progress, stage artifacts, candidate pool, review summary, and generated ideas without relying on frontend-only state.

#### Scenario: User starts an idea run with selected toolbox entries
- **WHEN** a user starts an idea generation run with selected toolbox tool IDs and a tool mode
- **THEN** the run config persists the selected tool context
- **AND** candidate generation receives the selected tool names, summaries, use cases, limitations, and linked evidence

#### Scenario: User requires toolbox usage
- **WHEN** the selected tool mode is `required`
- **THEN** generated candidates are prompted to use at least one selected toolbox entry
- **AND** selected proposals record which toolbox entries influenced the candidate when available
