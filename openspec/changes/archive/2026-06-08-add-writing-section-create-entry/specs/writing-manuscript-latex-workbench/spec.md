## ADDED Requirements

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
