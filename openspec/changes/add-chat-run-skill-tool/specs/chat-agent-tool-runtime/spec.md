## ADDED Requirements

### Requirement: Built-in research skill tool is available
The runtime SHALL provide `run_skill` as a read-only registered chat tool for executing built-in research skills with bounded inputs and outputs.

#### Scenario: Registered run skill tool exposes schema
- **WHEN** the chat tool registry returns available tool schemas
- **THEN** the schema list includes `run_skill`
- **AND** the tool is marked as non-side-effect

#### Scenario: Execute built-in research skill
- **WHEN** chat executes `run_skill` with a valid built-in skill id and task
- **THEN** the tool returns a bounded skill output
- **AND** the observation includes skill id, skill label, output format, and evaluation criteria metadata

#### Scenario: Unknown skill is rejected
- **WHEN** chat executes `run_skill` with an unknown skill id
- **THEN** the runtime rejects the call
- **AND** the observation lists available built-in skill ids

#### Scenario: Skill execution is read-only
- **WHEN** the planner selects `run_skill`
- **THEN** the runtime executes the skill without confirmation
- **AND** the skill does not mutate papers, folders, research projects, chat sessions, or files

#### Scenario: Deterministic routing handles explicit skill requests
- **WHEN** deterministic fallback receives an obvious prompt naming a built-in skill
- **THEN** it emits a `run_skill` call with the requested skill id and task
