## ADDED Requirements

### Requirement: Manuscript Support Files Are Interactive
The manuscript workbench SHALL expose `references.bib` and `figures/` as interactive support-file panels rather than static file-tree labels.

#### Scenario: User opens references from file structure
- **WHEN** the user clicks `references.bib` in the writing project file structure
- **THEN** the workbench navigates to a BibTeX panel for the selected writing project
- **AND** the panel displays BibTeX generated from the project's existing evidence cards.

#### Scenario: User copies generated BibTeX
- **WHEN** the BibTeX panel has generated reference content
- **THEN** the user can copy the complete BibTeX content
- **AND** the panel shows reference readiness metadata from the project's evidence cards.

#### Scenario: User refreshes generated BibTeX
- **WHEN** the user requests regeneration from the BibTeX panel
- **THEN** the system refreshes BibTeX from the current evidence cards without creating a separate reference source.

#### Scenario: User opens figures from file structure
- **WHEN** the user clicks `figures/` in the writing project file structure
- **THEN** the workbench navigates to a figure manifest panel for the selected writing project
- **AND** the panel displays figure entries stored in project metadata.

#### Scenario: User manages a figure manifest entry
- **WHEN** the user adds or updates a figure entry
- **THEN** the system persists the figure label, path, caption, and optional note in the writing project's metadata
- **AND** no physical figure file storage is required.

#### Scenario: User inserts a figure snippet
- **WHEN** a figure manifest entry exists
- **THEN** the workbench provides a LaTeX snippet for that figure
- **AND** the user can copy it or insert it into the active section.
