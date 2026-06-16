## ADDED Requirements

### Requirement: Chat tools are registered with typed schemas
The system SHALL provide a backend chat tool registry where each tool declares a stable name, label, argument schema, side-effect policy, and executor.

#### Scenario: Registered tools expose schemas
- **WHEN** the runtime asks the registry for available tools
- **THEN** it receives UI/model-safe schema summaries for each registered tool
- **AND** the summaries include whether the tool has side effects

#### Scenario: Unknown tool is rejected
- **WHEN** a model or caller requests a tool name that is not registered
- **THEN** the runtime rejects the call
- **AND** the observation lists allowed tool names for debugging

### Requirement: Tool arguments are validated before execution
The runtime SHALL validate tool arguments against each tool's declared schema before calling the executor.

#### Scenario: Invalid arguments do not execute
- **WHEN** a tool call has missing or invalid arguments
- **THEN** the runtime returns a rejected observation
- **AND** the tool executor is not called

### Requirement: Side-effect tools require explicit confirmation
The runtime SHALL block tools that mutate user data unless the request includes an explicit confirmation for that exact tool call.

#### Scenario: Import paper is planned autonomously
- **WHEN** an autonomous tool plan includes `import_paper`
- **THEN** the runtime returns `waiting_confirmation`
- **AND** no paper is imported

#### Scenario: User confirms import paper
- **WHEN** the user confirms a pending `import_paper` action for their own chat session
- **THEN** the runtime executes the import tool
- **AND** returns a completed observation with the imported paper reference

### Requirement: Tool execution emits observable trace events
The runtime SHALL emit structured trace events for planned, running, completed, failed, rejected, skipped, and waiting-confirmation tool states.

#### Scenario: Tool completes successfully
- **WHEN** a tool call runs successfully
- **THEN** the trace includes running and completed events
- **AND** the completed event includes a summary and result count

#### Scenario: Tool waits for confirmation
- **WHEN** a side-effect tool is blocked for confirmation
- **THEN** the trace includes a waiting-confirmation event
- **AND** the frontend can render an action affordance from the event details

### Requirement: Initial research tools are available
The runtime SHALL provide `search_papers`, `search_library`, and `import_paper` as the initial registered tools.

#### Scenario: Search papers
- **WHEN** chat requests a scholarly paper search tool call
- **THEN** `search_papers` returns bounded paper candidates and references without importing them

#### Scenario: Search library
- **WHEN** chat requests a local library search tool call
- **THEN** `search_library` returns bounded local paper references

#### Scenario: Import paper
- **WHEN** chat executes a confirmed `import_paper` tool call
- **THEN** the selected remote paper is added to the user's paper library using existing ingest behavior

### Requirement: Tool runtime is bounded
The runtime SHALL enforce bounded steps, bounded result counts, and graceful failure behavior.

#### Scenario: Planner returns too many calls
- **WHEN** the planner returns more tool calls than the runtime step limit
- **THEN** the runtime executes only the allowed number
- **AND** records a stop reason indicating the limit

#### Scenario: Tool executor fails
- **WHEN** a tool executor raises an exception
- **THEN** the runtime returns a failed observation
- **AND** the chat request continues when a useful partial answer can still be generated
