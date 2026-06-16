# llm-tool-planner Specification

## Purpose
Let general chat use a model-driven planning loop to select registered research tools, process observations, preserve side-effect confirmation gates, and expose planner trace metadata.

## Requirements
### Requirement: LLM planner emits validated tool plans
The system SHALL provide a planner that asks the language model to choose registered chat tools using strict JSON and SHALL validate the returned tool calls before execution.

#### Scenario: Planner returns valid actions
- **WHEN** the model returns a JSON object with an `actions` array containing registered tool calls
- **THEN** the backend converts those actions into typed chat tool calls
- **AND** each call is executed only through the shared tool registry validation path

#### Scenario: Planner returns malformed JSON
- **WHEN** the model planner response is not parseable as the required JSON object
- **THEN** the backend records a planner rejection or failure trace event
- **AND** the chat request falls back to deterministic planning when deterministic actions are available

#### Scenario: Planner requests unavailable or invalid tools
- **WHEN** the model planner requests an unknown tool or invalid arguments
- **THEN** the backend rejects those calls without executing tool side effects
- **AND** the trace includes enough detail to diagnose the rejected planner output

### Requirement: Planner loop uses observations for bounded follow-up planning
The system SHALL support a bounded action/observation loop where completed tool observations can be supplied to the planner for one or more follow-up rounds.

#### Scenario: Planner performs follow-up retrieval
- **WHEN** the first planner round returns a completed tool observation and the planner has remaining budget
- **THEN** the next planner prompt can include compact observation summaries
- **AND** the planner may return additional validated actions or signal final readiness

#### Scenario: Planner reaches round budget
- **WHEN** the planner consumes the configured maximum planning rounds
- **THEN** the loop stops
- **AND** the trace records a stop reason indicating the round limit

#### Scenario: Planner stops after enough evidence
- **WHEN** the planner returns no actions and signals final readiness
- **THEN** the loop stops with a completed stop reason
- **AND** the final language-model answer receives the accumulated bounded tool context

### Requirement: Planner preserves side-effect confirmation gates
The planner SHALL NOT execute mutation tools unless the exact side-effect confirmation requirements of the shared runtime are satisfied.

#### Scenario: Planner proposes paper import
- **WHEN** the planner proposes `import_paper` without a matching user confirmation token
- **THEN** the runtime returns `waiting_confirmation`
- **AND** no paper is imported

#### Scenario: Planner loop pauses for confirmation
- **WHEN** any observation is waiting for confirmation
- **THEN** the planner loop stops
- **AND** the frontend can render the existing confirmation action from trace metadata

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

### Requirement: Planner trace is observable in chat
The system SHALL expose planner decisions, fallback usage, tool observations, and stop reasons through the existing chat tool trace metadata.

#### Scenario: Streamed answer uses planner
- **WHEN** a streamed chat answer uses the LLM planner
- **THEN** the stream metadata includes planner/tool trace steps before or with final answer generation
- **AND** the saved assistant message can reconstruct the same trace from persisted metadata

#### Scenario: Non-stream answer uses planner
- **WHEN** a non-stream chat answer uses the LLM planner
- **THEN** the response includes the planner/tool trace payload
- **AND** the message references visible to users exclude internal trace metadata

### Requirement: Planner can select expanded library tools
The planner SHALL include the expanded registered chat tools in its tool schema prompt and SHALL preserve confirmation gates for side-effect library actions.

#### Scenario: Planner sees library action tools
- **WHEN** the planner builds messages from the default chat tool registry
- **THEN** the registered tool schema prompt includes `read_pdf`, `add_to_folder`, and `create_research_project`

#### Scenario: Planner proposes read-only paper reading
- **WHEN** the planner selects `read_pdf` with valid local paper arguments
- **THEN** the runtime executes the read-only tool without confirmation
- **AND** the final answer receives bounded paper evidence context

#### Scenario: Planner proposes library mutation
- **WHEN** the planner selects `add_to_folder` or `create_research_project` without a matching confirmation token
- **THEN** the runtime returns `waiting_confirmation`
- **AND** the planner loop stops before any mutation is performed

#### Scenario: Deterministic fallback routes obvious library actions
- **WHEN** planner fallback is used for an obvious local paper reading or organization prompt
- **THEN** deterministic routing attempts the matching safe or confirmed tool call when required arguments are present
- **AND** otherwise chat continues without an empty tool trace
