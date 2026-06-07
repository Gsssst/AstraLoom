## ADDED Requirements

### Requirement: Pages Can Use A Shared Page Shell

The frontend SHALL provide a reusable page shell for consistent page-level title, subtitle, action, width, and content spacing inside the shared application layout.

#### Scenario: Page renders with shell
- **WHEN** a page is wrapped with the shared page shell
- **THEN** it exposes stable shell, header, title, subtitle, action, and body class hooks
- **AND** its content is constrained by a configurable maximum width.

#### Scenario: Page has no actions
- **WHEN** a page does not provide header actions
- **THEN** the shell still renders a coherent title and content layout without an empty action area.

### Requirement: Settings Uses Shared Page Shell

The Settings page SHALL adopt the shared page shell without changing its tabs or settings workflows.

#### Scenario: User opens settings
- **WHEN** the Settings page renders
- **THEN** the page uses the shared shell with a settings title, short subtitle, and the existing tabs as shell content.
