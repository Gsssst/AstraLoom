## MODIFIED Requirements

### Requirement: Active retrieval strategy is visible
The chat toolbar SHALL display a concise retrieval-strategy label derived from the active sources and the composer SHALL expose the selected generic tool mode.

#### Scenario: View mixed retrieval mode
- **WHEN** knowledge-base retrieval and web enhancement are both enabled
- **THEN** the toolbar displays a mixed retrieval label

#### Scenario: View tool execution trace
- **WHEN** a chat answer used the generic chat tool runtime
- **THEN** the chat message displays a collapsible tool execution trace with tool statuses and result counts

#### Scenario: View planner execution trace
- **WHEN** a chat answer used the LLM tool planner
- **THEN** the chat message displays planner decisions, fallback usage, tool statuses, and stop reason in the collapsible tool execution trace

#### Scenario: Select generic tool mode
- **WHEN** a user changes the generic tool mode in the chat composer
- **THEN** subsequent general-mode chat requests include the selected `tool_mode`
- **AND** the composer runtime label reflects automatic, disabled, or forced tool behavior

#### Scenario: Research Scout ignores generic tool mode
- **WHEN** the active assistant mode is Research Scout
- **THEN** generic `tool_mode` does not disable or force the Research Scout-specific retrieval pipeline
