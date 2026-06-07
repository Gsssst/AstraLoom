## ADDED Requirements

### Requirement: Paper Library Uses Work-Focused Shell
The paper library frontend SHALL expose search, import, collection, reading-status, and maintenance workflows inside a shared work-focused page shell.

#### Scenario: User opens the paper library
- **WHEN** a user opens the paper library
- **THEN** the page title, subtitle, and high-level actions are presented by the shared shell
- **AND** search source, filters, collection controls, result-state controls, and bulk actions remain available.

#### Scenario: User works in maintenance mode
- **WHEN** a user switches to knowledge-base maintenance
- **THEN** maintenance diagnostics remain visible in the paper page body without replacing the shared page shell.
