## ADDED Requirements

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
