## ADDED Requirements

### Requirement: Writing Workbench Uses Shared Shell
The writing frontend SHALL present assistant mode, page identity, and high-level workbench actions through the shared shell while preserving project editing and one-off writing tools.

#### Scenario: User opens paper writing mode
- **WHEN** a user opens the writing page in paper mode
- **THEN** the shared shell presents the writing page title, subtitle, and assistant mode control
- **AND** project tabs, evidence panels, section editor, export panel, and one-off writing tools remain reachable.

#### Scenario: User opens grant writing mode
- **WHEN** a user switches to grant mode
- **THEN** the shared shell remains in place
- **AND** grant drafting, review, innovation, and polishing tools remain reachable.
