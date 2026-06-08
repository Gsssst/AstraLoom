## ADDED Requirements

### Requirement: Manuscript Workbench Is Chapter Driven
The system SHALL provide a manuscript writing workbench organized around paper sections rather than standalone writing tools.

#### Scenario: User opens manuscript writing
- **WHEN** the user opens the manuscript writing mode
- **THEN** the primary surface shows a writing project list, section navigation, the active section editor, preview diagnostics, and section AI assistance.

#### Scenario: User selects a section
- **WHEN** the user selects a manuscript section
- **THEN** the editor, preview diagnostics, evidence actions, citation checks, claim safety checks, and AI assistant are scoped to that section.

### Requirement: Sections Support LaTeX Source Editing
The system SHALL treat each manuscript section body as editable LaTeX source.

#### Scenario: User edits a section
- **WHEN** the user edits a manuscript section
- **THEN** the editor labels the content as LaTeX source and preserves LaTeX commands, equations, citations, labels, tables, and figures.

#### Scenario: User exports manuscript
- **WHEN** the user exports the project as LaTeX
- **THEN** the system assembles section LaTeX bodies into a valid document skeleton.

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: User checks current section
- **WHEN** the user requests preview for the active section
- **THEN** the system compiles or validates the section inside a minimal LaTeX document wrapper
- **AND** returns success status, warnings, errors, and compiler log details.

#### Scenario: User checks entire manuscript
- **WHEN** the user requests preview for the whole manuscript
- **THEN** the system checks the assembled LaTeX export and returns diagnostics.

#### Scenario: LaTeX compiler is unavailable
- **WHEN** the runtime does not have a LaTeX compiler available
- **THEN** the UI shows a clear compiler-unavailable diagnostic instead of failing silently.

### Requirement: AI Assistance Is Scoped To Current Section
The manuscript workbench SHALL provide an AI assistant panel scoped to the active section.

#### Scenario: User opens section AI assistant
- **WHEN** the user opens AI assistance for a section
- **THEN** the assistant shows actions relevant to the section type, current LaTeX source, proposal brief, evidence cards, citation checks, and claim safety status.

#### Scenario: User asks AI to repair LaTeX
- **WHEN** the current section preview has compile errors
- **THEN** the AI assistant provides an action to explain and repair the section LaTeX without changing unrelated sections.

#### Scenario: User asks AI to draft a section
- **WHEN** the user requests a section draft
- **THEN** the assistant uses the selected section role and available project evidence rather than generating a disconnected generic writing output.
