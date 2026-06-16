## ADDED Requirements

### Requirement: Chat reading area uses available viewport space
The chat workspace SHALL allocate most of the available viewport to messages and SHALL use a wider desktop content rail for conversation content.

#### Scenario: Desktop chat has readable density
- **WHEN** a user views an active chat on a desktop-width viewport
- **THEN** message rows and the composer use a wide content rail
- **AND** vertical chrome around the toolbar, message list, and composer is compact enough to show more conversation content.

#### Scenario: Research Scout answer is long
- **WHEN** a Research Scout answer includes tool trace and candidate cards
- **THEN** the message area width and height allow more of the generated answer to be visible before scrolling.
