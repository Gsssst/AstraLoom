# global-command-palette Specification

## Purpose
TBD - created by archiving change add-global-command-palette. Update Purpose after archive.
## Requirements
### Requirement: Global command palette opens from keyboard and header
The frontend SHALL provide a global command palette that can be opened from the application header and from `Ctrl/⌘ + K`.

#### Scenario: User opens palette with keyboard
- **WHEN** a user presses `Ctrl+K` or `⌘+K` while the app is focused
- **THEN** the app displays the global command palette instead of redirecting directly to a page

#### Scenario: User opens palette from header
- **WHEN** a user activates the command palette trigger in the global header
- **THEN** the app displays the global command palette

#### Scenario: User closes palette
- **WHEN** a user presses Escape or cancels the command palette
- **THEN** the command palette closes without changing the current route

### Requirement: Command palette exposes grouped workflow commands
The command palette SHALL show grouped commands for primary navigation and common workflow actions.

#### Scenario: Palette opens without a query
- **WHEN** the command palette opens with an empty query
- **THEN** it displays primary route commands for chat, action center, project spaces, papers, research, writing, settings, and home where the current user is allowed to access them

#### Scenario: User selects a navigation command
- **WHEN** a user selects a route command
- **THEN** the palette closes and the app navigates to the command target

#### Scenario: User searches commands
- **WHEN** a user types text that matches a command title, subtitle, keyword, or group
- **THEN** the palette filters command results while preserving their group labels

### Requirement: Command palette searches lightweight resources
The command palette SHALL search lightweight existing resources without requiring a new backend endpoint.

#### Scenario: Authenticated user searches resources
- **WHEN** an authenticated user enters a non-empty query
- **THEN** the palette requests lightweight results from existing paper, research, workspace, and writing resource APIs where available
- **AND** matching resource commands appear alongside static commands

#### Scenario: Resource search fails
- **WHEN** one or more resource search requests fail
- **THEN** the palette keeps static commands usable
- **AND** it shows a compact resource search unavailable state instead of blocking the whole palette

#### Scenario: User selects a resource result
- **WHEN** a user selects a paper, research project, workspace, or writing result
- **THEN** the palette closes and the app navigates to that resource or its best existing workflow route

### Requirement: Command palette supports keyboard-first operation
The command palette SHALL support keyboard-first operation for search and selection.

#### Scenario: Palette receives focus
- **WHEN** the command palette opens
- **THEN** focus moves to the command search input

#### Scenario: User confirms active result
- **WHEN** a user presses Enter while a command result is active
- **THEN** the app activates that result

#### Scenario: User navigates results with arrows
- **WHEN** a user presses ArrowDown or ArrowUp while results are available
- **THEN** the active result moves within the visible command result list

### Requirement: Command palette remains responsive
The command palette SHALL remain usable across desktop and narrow viewports.

#### Scenario: User opens palette on a narrow viewport
- **WHEN** the command palette opens below the medium breakpoint
- **THEN** it fits within the viewport without horizontal overflow
- **AND** command titles, subtitles, badges, and shortcuts remain readable

