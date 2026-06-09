## ADDED Requirements

### Requirement: Users can manage reusable research tools
The system SHALL provide a dedicated Toolbox space where authenticated users can create, browse, update, and delete reusable research tools independently from the paper library.

#### Scenario: User creates a tool
- **WHEN** an authenticated user creates a toolbox entry with name, kind, summary, use cases, limitations, tags, and maturity
- **THEN** the system persists the entry
- **AND** the toolbox list displays it as a reusable research tool

#### Scenario: User filters tools
- **WHEN** a user filters the toolbox by text, kind, tag, or maturity
- **THEN** the toolbox list returns matching tool entries

#### Scenario: User edits a tool
- **WHEN** an authenticated user updates a toolbox entry
- **THEN** the system persists the changed fields without removing linked paper evidence

### Requirement: Toolbox entries can cite source papers
The system SHALL allow toolbox entries to link to source papers with relation labels and concise evidence notes.

#### Scenario: User links a paper to a tool
- **WHEN** a user links a paper to a toolbox entry with a relation and evidence note
- **THEN** the tool detail displays the paper as source evidence
- **AND** the paper detail can display that linked toolbox entry

#### Scenario: User removes a paper link
- **WHEN** a user removes a paper link from a toolbox entry
- **THEN** the toolbox entry remains available
- **AND** the paper no longer appears as evidence for that tool
