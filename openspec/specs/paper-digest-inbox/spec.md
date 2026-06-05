# paper-digest-inbox Specification

## Purpose
TBD - created by archiving change paper-digest-inbox. Update Purpose after archive.
## Requirements
### Requirement: Users can browse paper digests in a dedicated inbox
The system SHALL provide an authenticated paper-library inbox that lists the user's digest notifications in reverse chronological order with the digest title, delivery time, keywords, generated summary, and recommended papers.

#### Scenario: User opens the digest inbox
- **WHEN** an authenticated user opens the paper digest inbox
- **THEN** the system displays that user's digest notifications newest first

#### Scenario: Historical sparse digest remains readable
- **WHEN** a historical digest only contains paper titles and arXiv identifiers
- **THEN** the inbox still displays its summary and available paper information without failing

### Requirement: New digests preserve actionable paper metadata
The system SHALL store structured metadata for recommended papers in newly generated digest notifications, including title, arXiv identifier, authors, year, and abstract snippet when available.

#### Scenario: Scheduled or manual digest contains papers
- **WHEN** the digest service creates a notification with matching arXiv papers
- **THEN** the notification metadata contains the structured recommendation fields required by the inbox

### Requirement: Users can act on individual digest recommendations
The paper digest inbox SHALL allow an authenticated user to open the arXiv abstract page, open the arXiv PDF, and add each recommended paper to the personal paper library independently.

#### Scenario: User adds a recommended paper
- **WHEN** the user clicks the add-to-library action on a recommendation card
- **THEN** the system resolves the arXiv paper through the existing personal ingestion workflow and updates the card to show that it has been added

### Requirement: Digest unread state integrates with global notifications
The system SHALL allow digest notifications to be marked as read without marking unrelated notifications as read, and SHALL refresh the visible global unread badge after a digest read action.

#### Scenario: User reads digest inbox history
- **WHEN** the user marks digest notifications as read from the inbox
- **THEN** only unread digest notifications are updated and the global unread badge refreshes

#### Scenario: User clicks header digest notification
- **WHEN** the user clicks a digest notification in the header popover
- **THEN** the digest is marked read and the browser navigates to the paper digest inbox

### Requirement: Paper library exposes the digest inbox
The paper library SHALL provide a visible entry action for the digest inbox and SHALL display an unread digest badge when unread digest notifications exist.

#### Scenario: Unread digest exists
- **WHEN** the user has at least one unread digest notification
- **THEN** the paper-library digest entry shows the unread digest count

