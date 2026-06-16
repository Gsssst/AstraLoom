## ADDED Requirements

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
