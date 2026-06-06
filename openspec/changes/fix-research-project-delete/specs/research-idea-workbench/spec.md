## ADDED Requirements

### Requirement: Project deletion cleans up workbench state
The system SHALL allow an authenticated project owner to delete a research project even when it has persisted Idea Workbench runs, selected proposals, and proposal lineage metadata.

#### Scenario: Owner deletes project with workbench runs
- **WHEN** an authenticated owner deletes a research project that has associated workbench runs and generated ideas
- **THEN** the delete request succeeds
- **AND** the project-owned workbench runs and generated ideas are removed

#### Scenario: Non-owner cannot delete project workbench state
- **WHEN** an authenticated user requests deletion of a research project they do not own
- **THEN** the system returns `404`
- **AND** the project, workbench runs, and ideas are preserved
