## MODIFIED Requirements

### Requirement: Chat controls have a consistent visual hierarchy
The chat toolbar SHALL group export, search, retrieval, model, and status controls into a compact secondary control area while keeping the current conversation title visually primary. Assistant mode switching SHALL be available in the composer because it controls the next message being sent. Toolbar controls SHALL use restrained workbench styling instead of glossy, over-rounded, or purple-dominant decorative treatments.

#### Scenario: View the chat toolbar
- **WHEN** a user opens the chat workspace
- **THEN** the conversation title is visually distinct and chat controls appear as a cohesive compact group
- **AND** active controls are legible without dominating the toolbar
- **AND** the assistant mode selector does not appear as a top-toolbar control

### Requirement: Composer is the primary interaction surface
The chat composer SHALL visually group attachments, message input, upload action, assistant mode switcher, runtime state, and send action into a cohesive bottom editor. The composer SHALL use restrained borders, stable dimensions, and a clear send affordance rather than oversized glossy shadows or nested card styling.

#### Scenario: Compose a chat message
- **WHEN** a user views the bottom of the chat workspace
- **THEN** upload, input, assistant mode switcher, runtime state, and send appear as one clear interaction area

#### Scenario: Switch assistant mode from the composer
- **WHEN** a user opens the composer mode control
- **THEN** the user can choose normal conversation or Research Scout without moving to the toolbar

#### Scenario: Use the integrated editor
- **WHEN** a user prepares a message
- **THEN** upload appears as a lightweight leading icon and send appears as a compact trailing emphasis action within the same editor container

#### Scenario: View the composer on mobile
- **WHEN** the chat workspace is opened on a mobile-width viewport
- **THEN** composer text and controls fit without overlapping or pushing the usable input area off screen
