## ADDED Requirements

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
The planner SHALL preserve deterministic tool routing as a fallback for obvious tool prompts.

#### Scenario: Planner is unavailable
- **WHEN** the planner LLM call fails or returns unusable output
- **THEN** the backend executes the deterministic plan if one exists
- **AND** the trace marks that fallback planning was used

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
