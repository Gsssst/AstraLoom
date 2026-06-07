# paper-bulk-actions-export Specification

## Purpose
Define how the paper library handles selected-paper bulk actions, including grouped toolbar behavior, client-side metadata export, reading-status updates, operation feedback, and responsive layout.
## Requirements
### Requirement: Paper library exposes a structured selected-paper bulk bar
The paper library SHALL display a structured bulk action bar when one or more local papers are selected.

#### Scenario: User selects local papers
- **WHEN** a user selects one or more local paper cards
- **THEN** the paper library displays a bulk action bar with the selected count
- **AND** the bar groups collection, reading-status, export, report, and clear-selection actions

#### Scenario: User clears selection
- **WHEN** a user activates the clear-selection action
- **THEN** all selected paper IDs are cleared
- **AND** the bulk action bar is hidden

### Requirement: User can export selected papers
The paper library SHALL allow users to export selected local papers in BibTeX, Markdown, and JSON formats.

#### Scenario: User exports selected papers as BibTeX
- **WHEN** a user selects papers and chooses BibTeX export
- **THEN** the browser downloads a `.bib` file for the selected papers

#### Scenario: User exports selected papers as Markdown
- **WHEN** a user selects papers and chooses Markdown export
- **THEN** the browser downloads a `.md` file containing selected paper metadata and abstracts

#### Scenario: User exports selected papers as JSON
- **WHEN** a user selects papers and chooses JSON export
- **THEN** the browser downloads a `.json` file containing selected paper metadata

### Requirement: User can bulk update selected paper reading status
The paper library SHALL allow an authenticated user to set a reading status on selected local papers.

#### Scenario: User marks selected papers as reading
- **WHEN** a user selects papers and chooses the "reading" status
- **THEN** each selected paper is updated through the existing reading-status workflow
- **AND** the paper list reflects the updated status for successful items

#### Scenario: Bulk status update partially fails
- **WHEN** some selected paper status updates fail
- **THEN** the paper library shows a success/failure summary
- **AND** successfully updated papers remain updated

### Requirement: Bulk operations report actionable outcomes
The paper library SHALL provide clear feedback for multi-step selected-paper operations.

#### Scenario: Bulk collection add completes
- **WHEN** selected papers are added to a collection
- **THEN** the user sees how many papers were added and skipped

#### Scenario: Bulk export has no matching loaded papers
- **WHEN** selected IDs no longer match papers loaded in the current result set
- **THEN** the paper library explains that export cannot proceed
- **AND** selection remains unchanged so the user can adjust the view or clear it

### Requirement: Bulk action bar remains responsive
The selected-paper bulk action bar SHALL remain usable across desktop and narrow viewports.

#### Scenario: User selects papers on a narrow viewport
- **WHEN** the bulk action bar appears below the medium breakpoint
- **THEN** controls wrap within the viewport without horizontal overflow
