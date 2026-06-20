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

