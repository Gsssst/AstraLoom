# Capability: Paper Annotation and Reading Loop

## ADDED Requirements

### Requirement: Personal PDF Annotations

The system SHALL let authenticated users persist selected PDF text as personal paper annotations.

#### Scenario: User saves selected PDF text

- **GIVEN** a user is viewing a paper detail page with selected PDF text
- **WHEN** the user saves the selection as an annotation
- **THEN** the annotation is persisted under the current user's paper state
- **AND** the paper is saved for the user
- **AND** existing notes, chat history, tags, and reading status remain intact

### Requirement: Annotation List and Reuse

The paper detail page SHALL display saved annotations and allow them to be reused in AI chat.

#### Scenario: User asks about a saved annotation

- **GIVEN** a paper has saved annotations
- **WHEN** the user chooses to ask AI about one annotation
- **THEN** the annotation text is added as quote context for the paper chat
- **AND** the normal paper chat stream is used

### Requirement: Annotation Deletion

The system SHALL let users delete their own annotations.

#### Scenario: User deletes an annotation

- **GIVEN** a saved annotation exists
- **WHEN** the user deletes it
- **THEN** that annotation is removed
- **AND** other personal paper state remains unchanged

### Requirement: Digest to Reading Queue

The digest center SHALL let users send recommended papers into their reading queue.

#### Scenario: User adds a recommended paper to unread queue

- **GIVEN** a digest recommendation has remote paper metadata
- **WHEN** the user clicks `加入待读`
- **THEN** the paper is ingested into the user's library if needed
- **AND** its read status is set to `unread`
- **AND** the UI indicates it has entered the reading queue

### Requirement: Start Reading from Digest

The digest center SHALL let users start reading a recommended paper directly.

#### Scenario: User starts reading from digest center

- **GIVEN** a digest recommendation is visible
- **WHEN** the user clicks `开始阅读`
- **THEN** the paper is ingested if needed
- **AND** its read status is set to `reading`
- **AND** the user can navigate to the local paper detail page
