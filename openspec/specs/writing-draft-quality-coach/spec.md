# writing-draft-quality-coach Specification

## Purpose
TBD - created by archiving change writing-draft-quality-coach. Update Purpose after archive.
## Requirements
### Requirement: Writing sections can be quality checked
The system SHALL provide deterministic section-level draft quality diagnostics.

#### Scenario: User checks a populated section
- **WHEN** an authenticated user checks a writing section with text
- **THEN** the response includes overall score, status label, summary, dimension checks, and rewrite actions

#### Scenario: User checks an empty or very short section
- **WHEN** the section is empty or too short
- **THEN** the response marks it as incomplete and recommends drafting a claim, adding evidence, and expanding structure

### Requirement: Quality diagnostics cover core academic writing dimensions
Quality diagnostics SHALL evaluate claim clarity, evidence presence, comparison, research gap, and section structure.

#### Scenario: Section lacks evidence or citations
- **WHEN** a section has no citation markers or evidence language
- **THEN** the evidence dimension is marked weak and suggests adding evidence cards or citations

#### Scenario: Section lacks comparison or gap
- **WHEN** a section does not mention baselines, comparison, limitations, or gaps
- **THEN** the relevant dimensions are marked weak and include rewrite hints

### Requirement: Writing UI surfaces quality coaching
The writing UI SHALL let users run quality checks from the section editor and display actionable results.

#### Scenario: User runs quality check in editor
- **WHEN** the user clicks quality check
- **THEN** the section editor shows overall status, dimension tags, explanations, and rewrite hints

