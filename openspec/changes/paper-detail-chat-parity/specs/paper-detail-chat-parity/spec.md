## ADDED Requirements

### Requirement: Paper chat always prioritizes the current paper
The paper-detail assistant SHALL include the open paper as mandatory primary context regardless of optional retrieval settings.

#### Scenario: Related-paper retrieval disabled
- **WHEN** a user disables the paper-library enhancement and asks a paper question
- **THEN** the assistant still answers from the open paper context

### Requirement: Paper chat supports optional mixed retrieval
The paper-detail assistant SHALL support related-paper library retrieval, web enhancement, and bounded retrieval depth settings.

#### Scenario: Web enhancement enabled
- **WHEN** a user enables web enhancement in paper-detail chat
- **THEN** the UI selects deep retrieval and the backend augments the current paper with online sources

#### Scenario: Related-paper library and web enhancement enabled
- **WHEN** both enhancements are enabled
- **THEN** the backend augments the current paper with bounded related-paper and online context

### Requirement: Paper chat uses robust streamed responses
The paper-detail assistant SHALL consume buffered JSON SSE events and SHALL show progress text while a request is pending.

#### Scenario: Stream frame crosses network chunks
- **WHEN** an answer event arrives across multiple network chunks
- **THEN** the frontend reconstructs the complete event before displaying its content

#### Scenario: Model returns no visible answer
- **WHEN** the model produces no visible content after retry
- **THEN** the paper chat displays a visible fallback instead of an empty answer bubble
