# research-toolbox Specification

## Purpose
Capture reusable research methods, tools, algorithms, datasets, metrics, and protocols as inspectable assets that can be linked to source papers and reused during idea generation.

## Requirements
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

### Requirement: Built-in research skills are inspectable toolbox assets
The system SHALL expose built-in research skills as structured toolbox assets that can be called by chat through the shared tool runtime.

#### Scenario: List built-in research skills
- **WHEN** backend code asks for built-in research skills
- **THEN** it receives stable skill definitions containing id, label, description, allowed tool hints, output format, and evaluation criteria

#### Scenario: Built-in skills cover core research workflows
- **WHEN** the built-in registry is initialized
- **THEN** it includes skills for paper scouting, method comparison, experiment planning, survey drafting, figure interpretation, and rebuttal help

#### Scenario: Skill definitions remain declarative
- **WHEN** a built-in skill is loaded
- **THEN** the definition is data-only guidance
- **AND** it does not execute arbitrary code or bypass chat tool validation
