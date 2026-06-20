# paper-push-center-chat-share-feed Specification

## Purpose
TBD - created by archiving change collapse-paper-chat-share-cards. Update Purpose after archive.
## Requirements
### Requirement: Paper chat share feed remains scannable with multiple shares
The paper push center SHALL keep multiple paper chat share items scannable by not expanding all shared content at once, and SHALL expose discussion and status controls only when an individual share card is expanded.

#### Scenario: Multiple shares exist
- **WHEN** the page renders multiple `paper_chat_share` notifications
- **THEN** each notification occupies a compact card until individually expanded

#### Scenario: User expands a share with discussion
- **WHEN** the user expands a paper chat share card
- **THEN** the card shows the selected shared messages and a lightweight discussion area
- **AND** the user can view comments, post a comment, and update their share status without leaving the push center

#### Scenario: User keeps share collapsed
- **WHEN** a paper chat share card remains collapsed
- **THEN** the page does not render the full discussion thread inline
- **AND** the feed remains compact enough to scan multiple shares

### Requirement: Expanded paper chat shares expose note settlement
The paper push center SHALL let users save an expanded paper chat share discussion into the corresponding paper note without leaving the feed.

#### Scenario: User saves an expanded share discussion
- **WHEN** the user expands a paper chat share card and chooses to settle the discussion
- **THEN** the client calls the settlement API for that share notification
- **AND** the card shows loading feedback while the save is in progress
- **AND** the user receives confirmation when the note update succeeds

#### Scenario: Settlement fails
- **WHEN** the settlement API rejects the request
- **THEN** the paper push center shows the returned error through the existing API error display pattern
- **AND** the expanded share content remains visible

