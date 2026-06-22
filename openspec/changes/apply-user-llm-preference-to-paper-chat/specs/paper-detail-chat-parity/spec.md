## ADDED Requirements

### Requirement: Paper chat honors user LLM preference
The paper-detail AI Q&A endpoints SHALL use the authenticated user's saved LLM provider/model preference when generating paper answers.

#### Scenario: User selected an OpenAI-compatible model
- **WHEN** an authenticated user has saved `openai-compatible` and `gpt-5.5` as their model preference
- **AND** the user asks a question through paper-detail AI Q&A
- **THEN** the backend binds that preference before invoking the LLM service
- **AND** the generated answer uses the OpenAI-compatible provider when it is configured.

#### Scenario: User has no valid preference
- **WHEN** an authenticated user has no saved model preference or the saved option is not configured
- **THEN** paper-detail AI Q&A falls back to the server default model selection.

#### Scenario: Streaming paper answer
- **WHEN** the user asks through the streaming paper Q&A endpoint
- **THEN** the request-scoped LLM preference is set before streaming generation begins.
