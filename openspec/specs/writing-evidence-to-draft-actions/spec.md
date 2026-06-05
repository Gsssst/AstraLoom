# writing-evidence-to-draft-actions Specification

## Purpose
TBD - created by archiving change writing-evidence-to-draft-actions. Update Purpose after archive.
## Requirements
### Requirement: Evidence cards can insert citation markers into drafts

The writing UI SHALL allow evidence citation markers to be inserted into the currently edited section.

#### Scenario: User has focused a section

- **GIVEN** a user is editing a writing project section
- **AND** project evidence cards are available
- **WHEN** the user clicks insert on an evidence card
- **THEN** the evidence marker is appended to the focused section content
- **AND** the section is persisted through the existing section update API

#### Scenario: No section is focused

- **GIVEN** no section has focus
- **WHEN** the user inserts an evidence marker
- **THEN** the system inserts into the first editable section
- **AND** notifies the user about the fallback target

### Requirement: Projects can generate an evidence-backed Related Work table

The system SHALL generate a deterministic Related Work comparison table from a writing project's evidence cards.

#### Scenario: Project has local and external evidence

- **GIVEN** a writing project has evidence cards
- **WHEN** the client requests an evidence Related Work table
- **THEN** the response includes a Markdown table
- **AND** each row includes citation marker, title, year, evidence role, local status, and suggested writing use
- **AND** coverage metadata reports local and external evidence counts

#### Scenario: Evidence coverage is low

- **GIVEN** a project has no evidence or mostly external-only evidence
- **WHEN** the evidence table is generated
- **THEN** the response includes warnings that the table should not be treated as verified final writing evidence

### Requirement: Evidence tables can be written back to project sections

The writing UI SHALL let users write a generated evidence table into the best matching project section.

#### Scenario: Comparison table section exists

- **GIVEN** a project contains a `Related Work Comparison Table` section
- **WHEN** the user writes the generated evidence table back
- **THEN** that section is updated with the generated Markdown

#### Scenario: Comparison table section is missing

- **GIVEN** a project does not contain a comparison table section
- **WHEN** the user writes the generated table back
- **THEN** the system falls back to a `Related Work` section when available
- **AND** otherwise copies the table for manual use

