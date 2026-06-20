# paper-chat-share-discussion-settlement Specification

## Purpose
TBD - created by archiving change save-paper-share-discussion-to-notes. Update Purpose after archive.
## Requirements
### Requirement: Share participants can settle discussions into paper notes
The system SHALL let an authorized paper chat share participant append a structured snapshot of the share and its discussion to their personal note for the shared paper.

#### Scenario: Participant saves a discussion to notes
- **WHEN** a participant requests to save a paper chat share discussion to notes
- **THEN** the system appends a Markdown block to that user's personal paper note
- **AND** the block includes the paper title, sender note when present, selected shared messages, discussion comments, status summary, saved timestamp, and source thread identifier
- **AND** existing personal note content for that paper remains before the new block

#### Scenario: Share has no local paper
- **WHEN** a participant requests to save a paper chat share discussion that is not linked to a local paper
- **THEN** the system rejects the request with a clear validation error
- **AND** no paper note is created

#### Scenario: Unauthorized user saves a discussion
- **WHEN** a user who is not a share participant requests to save the discussion
- **THEN** the system rejects access without exposing share content

### Requirement: Settlement response confirms note update
The system SHALL return enough information for the client to confirm the discussion was saved without reloading the paper detail page.

#### Scenario: Save succeeds
- **WHEN** a discussion is appended to paper notes
- **THEN** the response includes the local paper id, source thread id, saved timestamp, appended Markdown block, and updated note length

