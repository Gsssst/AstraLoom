## MODIFIED Requirements

### Requirement: Chat controls have a consistent visual hierarchy
The chat toolbar SHALL group chat modes, export, search, retrieval, and status controls into a compact secondary control area while keeping the current conversation title visually primary. Toolbar controls SHALL use restrained workbench styling instead of glossy, over-rounded, or purple-dominant decorative treatments.

#### Scenario: View the chat toolbar
- **WHEN** a user opens the chat workspace
- **THEN** the conversation title is visually distinct and chat controls appear as a cohesive compact group
- **AND** active controls are legible without dominating the toolbar

### Requirement: Session browsing is compact and scannable
The chat session list SHALL present conversation title, preview, and timestamp in compact rows with a subtle selected state. On desktop, the collapsed rail and expanded panel SHALL feel like a product navigation surface with restrained borders and minimal shadow.

#### Scenario: Scan conversation history
- **WHEN** a user views the session sidebar
- **THEN** each session row shows a readable title, short preview, and timestamp without excessive vertical spacing

#### Scenario: Delete a session
- **WHEN** a user hovers a desktop session row or views the active session
- **THEN** the delete affordance becomes available without dominating every session row

#### Scenario: Use the collapsed desktop rail
- **WHEN** a desktop user is not interacting with the session sidebar
- **THEN** the sidebar remains a compact rail that does not visually compete with the chat content

### Requirement: Composer is the primary interaction surface
The chat composer SHALL visually group attachments, message input, upload action, mode state, runtime state, and send action into a cohesive bottom editor. The composer SHALL use restrained borders, stable dimensions, and a clear send affordance rather than oversized glossy shadows or nested card styling.

#### Scenario: Compose a chat message
- **WHEN** a user views the bottom of the chat workspace
- **THEN** upload, input, mode state, runtime state, and send appear as one clear interaction area

#### Scenario: Use the integrated editor
- **WHEN** a user prepares a message
- **THEN** upload appears as a lightweight leading icon and send appears as a compact trailing emphasis action within the same editor container

#### Scenario: View the composer on mobile
- **WHEN** the chat workspace is opened on a mobile-width viewport
- **THEN** composer text and controls fit without overlapping or pushing the usable input area off screen

## ADDED Requirements

### Requirement: Chat message stream uses a professional workbench canvas
The chat workspace SHALL present the message stream on a calm neutral canvas with readable message widths, restrained assistant surfaces, and reference strips that attach to answers without looking like floating decorative cards.

#### Scenario: Read an assistant answer
- **WHEN** a user reads an assistant message with references
- **THEN** the answer, actions, and reference strip appear as a coherent work artifact
- **AND** the message surface avoids excessive radius, gradient, and shadow treatment

#### Scenario: Read a user prompt
- **WHEN** a user reads their own message
- **THEN** the prompt is visually distinct from assistant output without using oversized or glossy decoration
