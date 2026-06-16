## MODIFIED Requirements

### Requirement: Tool runtime is bounded
The runtime SHALL enforce bounded steps, bounded result counts, bounded planner-driven iterations, and graceful failure behavior.

#### Scenario: Planner returns too many calls
- **WHEN** the planner returns more tool calls than the runtime step limit
- **THEN** the runtime executes only the allowed number
- **AND** records a stop reason indicating the limit

#### Scenario: Planner loop reaches round limit
- **WHEN** the planner-driven action/observation loop reaches its configured round limit
- **THEN** the runtime stops additional planning
- **AND** preserves completed observations for the final answer context

#### Scenario: Tool executor fails
- **WHEN** a tool executor raises an exception
- **THEN** the runtime returns a failed observation
- **AND** the chat request continues when a useful partial answer can still be generated
