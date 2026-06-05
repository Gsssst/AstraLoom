## ADDED Requirements

### Requirement: Clear chat is a secondary confirmed action
The chat workspace SHALL keep destructive conversation clearing out of the primary toolbar flow and SHALL require confirmation before deleting messages.

#### Scenario: Clear the current conversation
- **WHEN** a user chooses the clear action from the chat overflow menu
- **THEN** the application asks for confirmation before removing the current conversation messages

### Requirement: Chat controls have a consistent visual hierarchy
The chat toolbar SHALL group chat modes, export, and search controls into a compact secondary control area while keeping the current conversation title visually primary.

#### Scenario: View the chat toolbar
- **WHEN** a user opens the chat workspace
- **THEN** the conversation title is visually distinct and chat controls appear as a cohesive compact group

### Requirement: Session browsing is compact and scannable
The chat session list SHALL present conversation title, preview, and timestamp in compact rows with a subtle selected state.

#### Scenario: Scan conversation history
- **WHEN** a user views the session sidebar
- **THEN** each session row shows a readable title, short preview, and timestamp without excessive vertical spacing

#### Scenario: Delete a session
- **WHEN** a user hovers a desktop session row or views the active session
- **THEN** the delete affordance becomes available without dominating every session row

### Requirement: Empty chat state guides the first action
The empty chat state SHALL present a cohesive brand treatment, a short instruction, and suggestion actions close enough to the composer to guide the user.

#### Scenario: Open an empty conversation
- **WHEN** a conversation contains no messages
- **THEN** the workspace displays a centered lightweight introduction and actionable suggestions

### Requirement: Composer is the primary interaction surface
The chat composer SHALL visually group prompt shortcuts, attachments, message input, upload action, and send action into a cohesive rounded panel. The upload action, text input, and send action SHALL read as one integrated editor rather than separate bordered controls.

#### Scenario: Compose a chat message
- **WHEN** a user views the bottom of the chat workspace
- **THEN** prompt shortcuts, upload, input, and send appear as one clear interaction area

#### Scenario: Use the integrated editor
- **WHEN** a user prepares a message
- **THEN** upload appears as a lightweight leading icon and send appears as a compact trailing emphasis action within the same editor container
