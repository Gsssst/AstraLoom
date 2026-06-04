## ADDED Requirements

### Requirement: Create and manage writing projects

The system SHALL allow users to create writing projects with a title, optional description, and template type (ACL, CVPR, NeurIPS, ICML, NSFC, or blank). Each project SHALL contain ordered sections representing the paper structure. Projects SHALL be private to the creating user.

#### Scenario: Create new writing project with ACL template

- **WHEN** user creates a project titled "My Paper" with template "ACL"
- **THEN** the system SHALL auto-create sections: Abstract, Introduction, Related Work, Method, Experiments, Conclusion
- **AND** each section SHALL be empty and editable

#### Scenario: Create blank project

- **WHEN** user creates a project with template "blank"
- **THEN** the system SHALL create a project with no pre-defined sections
- **AND** the user SHALL be able to add sections manually

### Requirement: Section editing and reordering

The system SHALL support adding, editing, deleting, and reordering sections within a project. Each section SHALL have: title, content (Markdown), status (draft/writing/polished/complete), and word count. Section content SHALL be auto-saved on every change (debounced at 2 seconds).

#### Scenario: Reorder sections by drag-and-drop

- **WHEN** user moves "Related Work" section before "Method" section via drag-and-drop
- **THEN** the section order SHALL update in the database
- **AND** the UI SHALL reflect the new order immediately

#### Scenario: Track section completion status

- **WHEN** user marks "Introduction" section as "complete"
- **THEN** the project progress bar SHALL update to reflect the new completion percentage

### Requirement: Multi-format export

The system SHALL support exporting the complete project or selected sections to these formats: PDF (via LaTeX compilation), Word (.docx via python-docx), LaTeX (.tex with template), and Markdown (.md). Exports SHALL include a generated BibTeX file if the project has citations.

#### Scenario: Export to Word with formatting

- **WHEN** user exports project to Word format
- **THEN** the .docx file SHALL include headings, body text, and formatted citations
- **AND** figures SHALL be referenced as placeholders with their captions

#### Scenario: Export selected sections only

- **WHEN** user selects only "Introduction" and "Method" for export
- **THEN** the exported file SHALL contain only those two sections

### Requirement: Project progress tracking

The system SHALL display project-level progress based on section completion status. Progress SHALL be calculated as: completed sections / total sections. A dashboard view SHALL show: completion percentage, word count per section, last edited timestamp, and AI-generated suggestions count.

#### Scenario: Dashboard shows project status

- **WHEN** a project has 6 sections with 3 marked "complete", 2 "writing", 1 "draft"
- **THEN** the progress bar SHALL show 50% (3/6 complete)
- **AND** the dashboard SHALL list each section with its status icon and word count
