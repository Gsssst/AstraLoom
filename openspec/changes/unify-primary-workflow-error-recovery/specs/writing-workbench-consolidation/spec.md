## ADDED Requirements

### Requirement: Writing Workflows Show Persistent API Recovery
The writing frontend SHALL show persistent structured recovery guidance for failed project loading, citation, generation, polishing, section, evidence, citation-check, quality, export, template, pipeline, and grant-helper operations.

#### Scenario: Writing API action fails
- **WHEN** a writing or grant helper API action fails
- **THEN** the writing page displays structured recovery guidance from the shared API error helper
- **AND** existing draft, project, and tab state remains available.

#### Scenario: Writing action succeeds after failure
- **WHEN** a writing operation succeeds after an earlier failed operation
- **THEN** stale writing recovery guidance is cleared when the successful action resolves the failure.
