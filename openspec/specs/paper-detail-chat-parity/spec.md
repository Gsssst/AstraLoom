# paper-detail-chat-parity Specification

## Purpose
TBD - created by archiving change paper-detail-chat-parity. Update Purpose after archive.
## Requirements
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
The paper-detail assistant SHALL consume buffered JSON SSE events and SHALL show progress text while a request is pending. Paper-detail AI Q&A SHALL request a provider-aware long-output budget so reasoning-heavy paper answers are not constrained by generic chat defaults.

#### Scenario: Stream frame crosses network chunks
- **WHEN** an answer event arrives across multiple network chunks
- **THEN** the frontend reconstructs the complete event before displaying its content

#### Scenario: Model returns no visible answer
- **WHEN** the model produces no visible content after retry
- **THEN** the paper chat displays a visible fallback instead of an empty answer bubble

#### Scenario: DeepSeek paper Q&A uses long output budget
- **WHEN** the active provider is DeepSeek
- **AND** a user asks a paper-detail AI question
- **THEN** the backend requests up to 384000 output tokens for paper Q&A generation

#### Scenario: GPT-compatible paper Q&A uses long output budget
- **WHEN** the active provider is OpenAI-compatible
- **AND** a user asks a paper-detail AI question
- **THEN** the backend requests up to 128000 output tokens for paper Q&A generation
