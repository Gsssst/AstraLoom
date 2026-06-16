## MODIFIED Requirements

### Requirement: Mixed retrieval combines contexts
The backend SHALL add both knowledge-base and web context when both sources are enabled and SHALL degrade gracefully if web retrieval fails.

#### Scenario: Build mixed context
- **WHEN** a chat request enables knowledge-base retrieval and web enhancement
- **THEN** the language-model context includes bounded knowledge-base paper context and bounded web search context

#### Scenario: Web provider fails
- **WHEN** web retrieval is unavailable during a web-enhanced request
- **THEN** chat continues with the remaining available context instead of failing the request

#### Scenario: Tool observations add context
- **WHEN** the generic chat tool runtime returns completed observations with references
- **THEN** the backend may include those observations as bounded context for the final language-model answer
- **AND** the message metadata includes the corresponding tool trace

### Requirement: Active retrieval strategy is visible
The chat toolbar SHALL display a concise retrieval-strategy label derived from the active sources.

#### Scenario: View mixed retrieval mode
- **WHEN** knowledge-base retrieval and web enhancement are both enabled
- **THEN** the toolbar displays a mixed retrieval label

#### Scenario: View tool execution trace
- **WHEN** a chat answer used the generic chat tool runtime
- **THEN** the chat message displays a collapsible tool execution trace with tool statuses and result counts
