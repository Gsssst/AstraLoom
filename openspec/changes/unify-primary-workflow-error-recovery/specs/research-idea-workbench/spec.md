## ADDED Requirements

### Requirement: Research Workflows Show Persistent API Recovery
The research direction list and research project workbench frontends SHALL show persistent structured recovery guidance for failed project, idea, proposal, evidence, experiment, validation, and generation operations.

#### Scenario: Research direction action fails
- **WHEN** loading, creating, deleting, or seeding a research direction fails
- **THEN** the research direction page displays structured recovery guidance from the shared API error helper.

#### Scenario: Research project workbench action fails
- **WHEN** a research project workbench API operation fails
- **THEN** the project page displays structured recovery guidance while preserving the current workbench state.

#### Scenario: Workbench operation succeeds after failure
- **WHEN** a research operation succeeds after an earlier failed operation
- **THEN** stale research recovery guidance is cleared when appropriate.
