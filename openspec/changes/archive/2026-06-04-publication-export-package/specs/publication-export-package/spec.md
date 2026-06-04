# Capability: Publication Export Package

## ADDED Requirements

### Requirement: Writing projects expose export readiness

The system SHALL provide a readiness summary before exporting a writing project.

#### Scenario: Project has incomplete sections

- **GIVEN** a writing project has empty or very short sections
- **WHEN** the user requests export readiness
- **THEN** the response includes incomplete-section warnings
- **AND** the status is not `ready`

#### Scenario: Project has weak evidence coverage

- **GIVEN** a writing project has evidence cards with low local or BibTeX coverage
- **WHEN** the user requests export readiness
- **THEN** the response includes evidence coverage warnings
- **AND** reports local, external, and BibTeX-ready counts

### Requirement: Writing projects export a publication package

The system SHALL export a writing project as a coherent publication package.

#### Scenario: User exports package

- **GIVEN** an authenticated user owns a writing project
- **WHEN** they request the publication package
- **THEN** the response includes Markdown, LaTeX, BibTeX, reference list, file names, and readiness metadata

#### Scenario: User exports references

- **GIVEN** a writing project has associated papers
- **WHEN** the user exports references
- **THEN** the response includes a numbered reference list derived from real project papers

### Requirement: Frontend exposes export workflow

The frontend SHALL provide export controls in the writing project workspace.

#### Scenario: User opens a writing project

- **GIVEN** the writing project is selected
- **WHEN** the project management tab is shown
- **THEN** the user sees export readiness and copy/download actions for Markdown, BibTeX, LaTeX, references, and Word
