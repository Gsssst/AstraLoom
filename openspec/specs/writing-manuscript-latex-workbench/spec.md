# writing-manuscript-latex-workbench Specification

## Purpose
TBD - created by archiving change restructure-writing-manuscript-latex-workbench. Update Purpose after archive.
## Requirements
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

### Requirement: Manuscript Sections Can Be Created From The Workbench
The manuscript workbench SHALL provide a visible way to create a manuscript section when the project has no sections and when the project already has sections.

#### Scenario: User opens a project with no sections
- **WHEN** the manuscript workbench opens for a writing project with zero sections
- **THEN** the section navigation and empty editor state provide an action to create the first section.

#### Scenario: User creates a section
- **WHEN** the user creates a section from the manuscript workbench
- **THEN** the system persists the section on the writing project
- **AND** selects the new section as the active section for LaTeX source editing.

#### Scenario: User lacks edit permission
- **WHEN** a user without edit permission attempts to create a section
- **THEN** the system rejects the request and shows an actionable error instead of creating a local-only section.

### Requirement: Section Creation Uses Database-Compatible Project Identifiers
The manuscript workbench SHALL create sections using project identifiers that are compatible with the database column type.

#### Scenario: Project identifiers are UUID-backed
- **WHEN** a user creates a section for a writing project stored with a UUID project identifier
- **THEN** the section creation query uses a UUID-compatible value
- **AND** the section is persisted without a UUID/string operator error.

### Requirement: Manuscript Workbench Uses Space Efficiently
The manuscript workbench SHALL prioritize active section editing width and group sparse supporting panels together.

#### Scenario: User opens a manuscript project on a wide screen
- **WHEN** the manuscript workbench renders project selection, section navigation, active editor, and evidence cards
- **THEN** the active editor receives the main horizontal space
- **AND** project selection and evidence context are grouped into a compact side rail instead of occupying opposite sides.

### Requirement: Writing Section ORM Types Match UUID Schema
The manuscript workbench SHALL map UUID-backed writing section foreign keys using UUID-compatible ORM column types.

#### Scenario: Section creation compiles a project filter
- **WHEN** the backend builds the section creation query for a UUID-backed writing project
- **THEN** the `writing_sections.project_id` comparison is compiled as a UUID-compatible bind
- **AND** PostgreSQL does not receive a `VARCHAR` bind for the UUID column.

#### Scenario: Section polish history compiles a section filter
- **WHEN** the backend builds a polish history query for a UUID-backed writing section
- **THEN** the `polish_versions.section_id` comparison is compiled as a UUID-compatible bind
- **AND** PostgreSQL does not receive a `VARCHAR` bind for the UUID column.

### Requirement: Manuscript Support Rail Can Collapse
The manuscript workbench SHALL allow users to collapse and reopen the supporting project/evidence rail.

#### Scenario: User focuses on drafting on a wide screen
- **WHEN** the user collapses the support rail
- **THEN** the project selector and evidence cards are hidden from the main work surface
- **AND** the active manuscript editor receives additional horizontal space
- **AND** a visible reopen control remains available.

#### Scenario: User restores context
- **WHEN** the user reopens the support rail
- **THEN** the project selector and evidence cards return together
- **AND** the active manuscript editor remains available without losing the selected section.

