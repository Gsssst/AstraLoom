## ADDED Requirements

### Requirement: Research Scout chat uses agentic retrieval mode
The chat backend SHALL route Research Scout requests through the Research Scout agentic discovery workflow and SHALL preserve normal chat behavior for non-Research-Scout requests.

#### Scenario: User selects Research Scout mode
- **WHEN** the user sends a chat message with `assistant_mode=research_scout`
- **THEN** the backend invokes the Research Scout agent workflow
- **AND** the response metadata includes Research Scout candidates, references, retrieval diagnostics, and tool trace when available.

#### Scenario: User sends a normal chat request
- **WHEN** the user sends a chat message with normal assistant mode
- **THEN** the backend does not invoke the Research Scout agent workflow unless auto-routing identifies a paper discovery request
- **AND** existing knowledge-base and web retrieval behavior remains available.

### Requirement: Research Scout streams observable tool progress
The chat stream SHALL expose Research Scout tool progress events that reflect actual backend tool executions.

#### Scenario: Agent executes search tools
- **WHEN** Research Scout calls search or filtering tools during a streamed response
- **THEN** the frontend receives progress metadata for planned, running, completed, failed, skipped, or stop events
- **AND** the visible trace shows tool name, concise argument summary, provider/source, result count, and retry or failure reason when available.

#### Scenario: Agent finalizes candidates
- **WHEN** Research Scout finishes candidate preparation
- **THEN** the streamed assistant message includes final candidate cards
- **AND** the source strip shows only paper candidates used by Research Scout, not unrelated generic web pages.
