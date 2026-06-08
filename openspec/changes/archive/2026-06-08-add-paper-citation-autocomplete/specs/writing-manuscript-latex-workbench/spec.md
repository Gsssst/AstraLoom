## MODIFIED Requirements

### Requirement: Sections Support LaTeX Source Editing
The system SHALL treat each manuscript section body as editable LaTeX source.

#### Scenario: User receives paper citation suggestions
- **WHEN** the user types inside a LaTeX citation command such as `\cite{`
- **THEN** the editor offers citation suggestions from the selected writing project's evidence cards
- **AND** suggestions include enough paper metadata to distinguish entries.

#### Scenario: User inserts an evidence citation
- **WHEN** the user selects a citation suggestion
- **THEN** the editor inserts the project's citation marker into the citation command
- **AND** preserves the current draft content around the citation.
