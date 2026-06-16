## MODIFIED Requirements

### Requirement: Planner degrades to deterministic routing
The planner SHALL preserve deterministic tool routing as a fallback for obvious tool prompts and SHALL respect the caller's selected tool mode.

#### Scenario: Planner is unavailable in auto mode
- **WHEN** the planner LLM call fails or returns unusable output while tool mode is `auto`
- **THEN** the backend executes the deterministic plan if one exists
- **AND** the trace marks that fallback planning was used

#### Scenario: Planner returns no actions in auto mode
- **WHEN** the planner returns no actions and indicates the answer can proceed without tools while tool mode is `auto`
- **THEN** chat continues as a normal answer
- **AND** no deterministic fallback is forced

#### Scenario: Planner returns no actions in force mode
- **WHEN** the planner returns no actions while tool mode is `force`
- **THEN** the backend attempts deterministic planning if deterministic actions are available
- **AND** the trace marks that force-mode fallback was used

#### Scenario: Tools are disabled
- **WHEN** tool mode is `off`
- **THEN** the generic LLM tool planner and deterministic tool fallback are skipped
- **AND** chat continues with ordinary retrieval context only

#### Scenario: No planner or deterministic action applies
- **WHEN** neither the LLM planner nor deterministic routing produces actions
- **THEN** chat continues as a normal non-tool answer
- **AND** no empty tool trace is attached
