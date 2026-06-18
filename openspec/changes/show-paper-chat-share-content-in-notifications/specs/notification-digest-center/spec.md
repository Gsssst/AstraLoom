## ADDED Requirements

### Requirement: Notification popover supports rich paper chat share cards
The global notification popover SHALL support rich rendering for `paper_chat_share` notifications with selected-message metadata.

#### Scenario: Paper chat share notification has selected messages
- **WHEN** the notification item category is `paper_chat_share` and metadata includes `selected_messages`
- **THEN** the popover renders a paper-share preview instead of only a single-line description

#### Scenario: Paper chat share notification has no selected messages
- **WHEN** the notification item lacks selected-message metadata
- **THEN** the popover falls back to the existing content summary and source-paper navigation
