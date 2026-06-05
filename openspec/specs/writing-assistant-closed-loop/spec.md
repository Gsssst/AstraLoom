# writing-assistant-closed-loop Specification

## Purpose
TBD - created by archiving change writing-assistant-closed-loop. Update Purpose after archive.
## Requirements
### Requirement: Create Review Draft From Research Direction
The system SHALL allow an authenticated user to create a writing project from a research direction and SHALL prefill review-oriented sections using locally retrieved papers.

#### Scenario: Successful draft creation
- **WHEN** the user submits a non-empty research direction
- **THEN** the system creates a writing project with survey sections, stores source metadata, and returns the created project.

#### Scenario: No matching papers
- **WHEN** the system cannot retrieve relevant papers for the research direction
- **THEN** the system still creates a scaffolded project and clearly marks that evidence is insufficient.

### Requirement: Related Work Comparison Table
The system SHALL generate a Related Work comparison table for a research direction using retrieved papers.

#### Scenario: Generate table rows
- **WHEN** the user requests a comparison table for a topic
- **THEN** the response includes Markdown table content and structured rows containing paper, year, contribution, role, and comparison points.

### Requirement: Role-Aware Citation Recommendations
The system SHALL label citation recommendations by how they can be used in writing.

#### Scenario: Recommendation role labels
- **WHEN** the user requests citation recommendations for a sentence or paragraph
- **THEN** each recommendation includes a role, localized role label, role reason, match score, and match status.

### Requirement: Sentence Citation Match Check
The system SHALL check whether a citation exists and whether it matches a target sentence.

#### Scenario: Local paper match
- **WHEN** the user checks a sentence against a paper that exists in the local library
- **THEN** the system reports existence, source, match score, match status, and a human-readable explanation.

#### Scenario: Missing or weak citation
- **WHEN** the citation cannot be found or the sentence is weakly supported
- **THEN** the system reports the weakness transparently rather than claiming the citation is valid.

### Requirement: Writing Project Export Formats
The system SHALL export writing projects as Markdown, Word, and BibTeX.

#### Scenario: BibTeX export
- **WHEN** the user exports a writing project with `format=bibtex`
- **THEN** the response contains BibTeX entries for project-related papers resolved from project metadata or references.

