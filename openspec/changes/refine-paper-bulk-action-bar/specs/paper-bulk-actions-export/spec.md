## MODIFIED Requirements

### Requirement: Bulk action bar remains responsive
The selected-paper bulk action bar SHALL remain usable across desktop and narrow viewports without visual overlap between action groups.

#### Scenario: User selects papers on a narrow viewport
- **WHEN** the bulk action bar appears below the medium breakpoint
- **THEN** controls wrap within the viewport without horizontal overflow

#### Scenario: User selects papers with all action groups visible
- **WHEN** collection, reading-status, export, report, tagging, and clear-selection controls are visible at the same time
- **THEN** each action group remains visually separated
- **AND** labels and buttons do not overlap adjacent groups
- **AND** the toolbar may wrap to multiple rows instead of compressing controls into each other
