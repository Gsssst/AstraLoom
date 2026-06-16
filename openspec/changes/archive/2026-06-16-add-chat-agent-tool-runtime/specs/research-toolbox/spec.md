## MODIFIED Requirements

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

#### Scenario: Toolbox tools are eligible for agent runtime exposure
- **WHEN** a toolbox entry or future skill is marked as callable by chat
- **THEN** it is exposed through the shared chat agent tool runtime with a typed schema and side-effect policy
- **AND** it does not bypass tool validation or confirmation requirements
