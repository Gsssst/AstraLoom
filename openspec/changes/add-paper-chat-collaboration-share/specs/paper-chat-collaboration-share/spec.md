## ADDED Requirements

### Requirement: Paper chat answers can be shared to linked project spaces
The system SHALL let an authenticated user share a selected paper AI assistant answer to a project space only when the user is a member of that space and the paper is linked to that space.

#### Scenario: User lists available share targets
- **GIVEN** a paper is linked to one or more project spaces that include the current user
- **WHEN** the user opens the paper chat share modal
- **THEN** the system returns those spaces with id, name, role, member count, and share eligibility

#### Scenario: User shares an assistant answer
- **GIVEN** the current paper is linked to the selected project space
- **AND** the user is a member of that project space
- **WHEN** the user submits a selected AI answer with its paired question
- **THEN** other project-space members receive a paper chat share notification
- **AND** the selected workspace records a `paper_chat_shared` activity

#### Scenario: User tries to share to unrelated space
- **GIVEN** the selected project space is not linked to the paper or the user is not a member
- **WHEN** the user submits the share request
- **THEN** the system rejects the request without creating notifications

### Requirement: Shared paper chat insight cards preserve source context
The shared insight payload SHALL include the source paper, sender, workspace, user question, assistant answer, optional sender note, and bounded evidence references.

#### Scenario: Shared card is created
- **WHEN** a paper chat answer is shared successfully
- **THEN** notification metadata contains paper id, paper title, workspace id, workspace name, sender identity, question excerpt, answer excerpt, optional note, source path, and evidence reference summary

#### Scenario: Shared content is too large
- **WHEN** the submitted question, answer, note, or references exceed the allowed bounds
- **THEN** the system stores bounded excerpts that remain safe to render in notification and workspace activity views

### Requirement: Paper detail exposes a curated share action
The frontend SHALL expose a compact share action on completed assistant answer messages in paper detail chat.

#### Scenario: Assistant answer is complete
- **WHEN** a paper chat assistant message has finished streaming
- **THEN** the message actions include a share-to-members control

#### Scenario: No linked workspace exists
- **WHEN** the user opens the share modal and the paper has no linked project space available to the user
- **THEN** the modal explains that the paper must be linked to a project space before sharing

#### Scenario: Share succeeds
- **WHEN** the backend accepts the share request
- **THEN** the frontend shows the recipient count and refreshes the global unread-notification state
