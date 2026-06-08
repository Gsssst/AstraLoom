## ADDED Requirements

### Requirement: Manuscript And Survey Workflows Are Separated
The Writing page SHALL separate manuscript writing from survey/literature-review workflows.

#### Scenario: User opens paper writing mode
- **WHEN** the user opens paper writing mode
- **THEN** the default screen is the manuscript workbench and does not show survey draft creation as the primary action.

#### Scenario: User wants to create a survey
- **WHEN** the user chooses the survey workflow
- **THEN** the UI exposes literature-review, paper comparison, evidence table, and research-gap generation separately from manuscript section editing.

### Requirement: Template Setup Is Not The Main Manuscript Entry
The Writing page SHALL avoid making conference template selection the primary manuscript creation step.

#### Scenario: User creates a manuscript
- **WHEN** the user creates a manuscript project
- **THEN** the default path creates a chapter-based manuscript without requiring ACL/CVPR/NeurIPS template selection first.

#### Scenario: User prepares submission export
- **WHEN** the user needs official formatting
- **THEN** template/profile upload remains available from export or submission readiness rather than the main writing editor.
