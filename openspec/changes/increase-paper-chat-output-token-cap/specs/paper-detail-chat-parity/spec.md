## MODIFIED Requirements

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
