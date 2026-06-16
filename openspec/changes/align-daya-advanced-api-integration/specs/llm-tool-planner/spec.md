## MODIFIED Requirements

### Requirement: LLM planner emits validated tool plans
The system SHALL provide a planner that asks the language model to choose registered chat tools using strict JSON and SHALL validate the returned tool calls before execution. When the active provider supports OpenAI-compatible structured output, the planner SHALL request a JSON schema response instead of relying only on prompt instructions.

#### Scenario: Planner returns valid actions
- **WHEN** the model returns a JSON object with an `actions` array containing registered tool calls
- **THEN** the backend converts those actions into typed chat tool calls
- **AND** each call is executed only through the shared tool registry validation path

#### Scenario: Planner uses provider structured output
- **WHEN** the active model provider is OpenAI-compatible and configured
- **THEN** the planner request includes a JSON schema response format for the planner decision
- **AND** the returned content is parsed through the same validated planner schema before any tool is executed

#### Scenario: Planner returns malformed JSON
- **WHEN** the model planner response is not parseable as the required JSON object
- **THEN** the backend records a planner rejection or failure trace event
- **AND** the chat request falls back to deterministic planning when deterministic actions are available

#### Scenario: Planner requests unavailable or invalid tools
- **WHEN** the model planner requests an unknown tool or invalid arguments
- **THEN** the backend rejects those calls without executing tool side effects
- **AND** the trace includes enough detail to diagnose the rejected planner output
