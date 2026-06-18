## ADDED Requirements

### Requirement: Digest center APIs return paper push categories
The digest center API SHALL return notification categories that represent paper pushes, including daily digests and paper chat shares.

#### Scenario: List paper push notifications
- **WHEN** a user requests `/notifications/digests`
- **THEN** the response includes notifications with category `digest` and `paper_chat_share`

#### Scenario: Count unread paper push notifications
- **WHEN** a user requests `/notifications/digests/unread-count`
- **THEN** the response counts unread notifications with category `digest` and `paper_chat_share`
