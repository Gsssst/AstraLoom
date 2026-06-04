## ADDED Requirements

### Requirement: Convert Research Idea To Writing Draft
The system SHALL allow an authenticated user to create a writing project from an owned research Idea.

#### Scenario: Create draft from evidence-backed Idea
- **WHEN** the user requests a writing draft from an owned Idea with evidence
- **THEN** the system creates a writing project containing Idea context, evidence table, research gaps, and references.

#### Scenario: Create draft from Idea with weak evidence
- **WHEN** the Idea has no local evidence papers
- **THEN** the system still creates a writing project and marks the evidence status as insufficient.

### Requirement: Preserve Evidence Metadata
The system SHALL preserve source project, source Idea, and evidence paper metadata in the writing project.

#### Scenario: Metadata stored on writing project
- **WHEN** a writing project is created from a research Idea
- **THEN** project metadata includes source project ID, source Idea ID, evidence items, and local paper IDs where available.

### Requirement: Navigate To Created Writing Project
The frontend SHALL navigate users from a research Idea to the newly created writing project.

#### Scenario: Open created draft
- **WHEN** the user clicks "生成写作草稿" on a Proposal
- **THEN** the frontend calls the bridge endpoint and opens the writing page with the created project selected.
