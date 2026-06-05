# shared-layout-boundaries Specification

## Purpose
TBD - created by archiving change restore-shared-layout-boundaries. Update Purpose after archive.
## Requirements
### Requirement: Page workspaces remain contained below the global header
The application shell SHALL apply its shared layout spacing contract so page workspaces do not overlap global navigation controls.

#### Scenario: Chat workspace fills content without entering header
- **WHEN** an authenticated user opens the desktop chat workspace
- **THEN** the chat toolbar and session sidebar remain below the global header
- **AND** the chat toolbar actions do not overlap the global account controls

### Requirement: Shared responsive shell styles remain attached
The application shell SHALL retain the shared class hooks used by responsive desktop and mobile layout rules.

#### Scenario: Shell markup keeps required style hooks
- **WHEN** the shared application layout is rendered
- **THEN** the main layout, header, and content containers expose their responsive class hooks

### Requirement: Collapsed sidebar logo remains centered
The application shell SHALL horizontally center the compact logo icon within the collapsed desktop sidebar.

#### Scenario: Compact logo uses full sidebar width
- **WHEN** the desktop sidebar is collapsed
- **THEN** the logo click target spans the sidebar width
- **AND** the compact logo icon is horizontally centered

### Requirement: Selected chat session uses one visual marker
The chat session sidebar SHALL render a selected conversation with one left-side active marker.

#### Scenario: Active conversation avoids duplicated indicators
- **WHEN** a conversation is selected in the chat session sidebar
- **THEN** the selected item displays the short active marker
- **AND** no second full-height left border is rendered

