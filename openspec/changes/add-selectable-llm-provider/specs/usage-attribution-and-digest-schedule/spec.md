## ADDED Requirements

### Requirement: Usage records use active LLM model
The system SHALL record token usage against the model that served the request.

#### Scenario: Usage is recorded for selected model
- **WHEN** an LLM call succeeds using the OpenAI-compatible GPT-5.5 option
- **THEN** the token usage record uses the GPT-5.5 model identifier
