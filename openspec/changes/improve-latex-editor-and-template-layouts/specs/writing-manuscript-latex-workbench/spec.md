## MODIFIED Requirements

### Requirement: Sections Support LaTeX Source Editing
The system SHALL treat each manuscript section body as editable LaTeX source.

#### Scenario: User receives LaTeX command suggestions
- **WHEN** the user types a LaTeX command prefix such as `\c` in the section source editor
- **THEN** the editor offers matching command snippets such as `\cite{}`
- **AND** selecting a snippet inserts it into the section body without losing the user's current draft.

#### Scenario: User navigates command suggestions by keyboard
- **WHEN** LaTeX command suggestions are visible
- **THEN** the user can move through suggestions and apply one using keyboard controls.

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: Preview honors selected manuscript layout
- **WHEN** the user previews a manuscript with a selected single-column or double-column layout
- **THEN** the rendered LaTeX document uses the corresponding document class options before compilation.
