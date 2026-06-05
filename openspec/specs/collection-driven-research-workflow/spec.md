# collection-driven-research-workflow Specification

## Purpose
TBD - created by archiving change collection-driven-research-workflow. Update Purpose after archive.
## Requirements
### Requirement: Collections expose idea-readiness diagnostics

Personal paper collections SHALL report whether they are sufficiently prepared for idea exploration.

#### Scenario: User reviews a collection

- **GIVEN** a user owns a paper collection
- **WHEN** they request collection diagnostics
- **THEN** the response includes paper count, full-text coverage, embedding coverage, reading counts, readiness state, and warnings

### Requirement: Research ideas preserve collection provenance

Research directions created from collections SHALL preserve which collections contributed seed evidence.

#### Scenario: Idea generation uses collection seeds

- **GIVEN** a research direction was created with selected collection IDs
- **WHEN** the idea workbench collects seed evidence and persists ideas
- **THEN** seed evidence includes collection names
- **AND** generated ideas expose collection-source metadata in their referenced papers or evidence metadata

### Requirement: Remote papers can be ingested directly into a collection

The paper library SHALL allow users to put newly discovered remote papers into a selected collection without a second manual organization step.

#### Scenario: User adds a remote result to a collection

- **GIVEN** the user has selected a target collection
- **WHEN** they add a remote search result to the library
- **THEN** the paper is ingested
- **AND** the resulting local paper is added to the target collection
- **AND** the UI confirms both actions

