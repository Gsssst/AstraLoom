## ADDED Requirements

### Requirement: Paper Digest Inbox Uses Shared Page Shell

The paper digest inbox page SHALL use the shared page shell for page title, subtitle, action, width, and content spacing.

#### Scenario: User opens paper digest inbox
- **WHEN** the paper digest inbox renders
- **THEN** it uses the shared page shell with a digest title and subtitle
- **AND** the return-to-paper-library command is rendered as a page action.

## MODIFIED Requirements

### Requirement: Pages Can Use A Shared Page Shell

The frontend SHALL provide a reusable page shell for consistent page-level title, subtitle, action, width, and content spacing inside the shared application layout.

#### Scenario: Page renders with shell
- **WHEN** a page is wrapped with the shared page shell
- **THEN** it exposes stable shell, header, title, subtitle, action, and body class hooks
- **AND** its content is constrained by a configurable maximum width.

#### Scenario: Page has no actions
- **WHEN** a page does not provide header actions
- **THEN** the shell still renders a coherent title and content layout without an empty action area.
