## ADDED Requirements

### Requirement: Paper push center includes AI reading shares
The paper push center SHALL display paper AI reading share notifications alongside daily paper digest notifications.

#### Scenario: Recipient has paper chat share notifications
- **WHEN** the recipient opens the paper push center
- **THEN** `paper_chat_share` notifications are listed with sender, paper title, note, selected message excerpts, and an open-paper action

#### Scenario: Recipient has both digest and share notifications
- **WHEN** the paper push center loads
- **THEN** daily digest notifications and paper chat share notifications are sorted together by creation time

### Requirement: Paper push center read controls include share notifications
The paper push center SHALL count and mark read both daily digest and paper chat share notifications.

#### Scenario: Unread share exists
- **WHEN** the paper push center fetches unread count
- **THEN** unread `paper_chat_share` notifications are included

#### Scenario: User marks all paper pushes read
- **WHEN** the user clicks all-read in the paper push center
- **THEN** unread `digest` and `paper_chat_share` notifications are marked read
