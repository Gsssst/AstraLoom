# chat-retrieval-mode-coordination Specification

## Purpose
TBD - created by archiving change chat-retrieval-mode-coordination. Update Purpose after archive.
## Requirements
### Requirement: Web enhancement is a one-click action
The chat workspace SHALL automatically select deep retrieval when a user enables web enhancement and SHALL NOT require the user to disable knowledge-base retrieval.

#### Scenario: Enable web enhancement while knowledge base is active
- **WHEN** a user activates web enhancement while knowledge-base retrieval is enabled
- **THEN** the depth selector changes to deep and both retrieval sources remain active

#### Scenario: Use web enhancement without knowledge base
- **WHEN** a user disables knowledge-base retrieval while web enhancement remains active
- **THEN** the application continues to submit web-enhanced chat requests

### Requirement: Retrieval depth affects backend breadth
Chat requests SHALL submit a validated `search_depth` value and the backend SHALL use it to select bounded knowledge-base and web result counts.

#### Scenario: Submit deep retrieval
- **WHEN** a chat request uses `search_depth=deep`
- **THEN** the backend uses the configured deep retrieval breadth for enabled sources

#### Scenario: Reject invalid retrieval depth
- **WHEN** a chat request contains an unsupported retrieval depth
- **THEN** request validation rejects the payload

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
