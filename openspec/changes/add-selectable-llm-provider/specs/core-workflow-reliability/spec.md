## ADDED Requirements

### Requirement: Selectable LLM provider drives chat completions
The system SHALL route LLM calls through the currently selected provider/model while preserving the existing non-streaming and streaming chat wrapper behavior.

#### Scenario: DeepSeek remains the default provider
- **WHEN** no alternate provider is selected
- **THEN** LLM calls use the configured DeepSeek model, API base, and API key

#### Scenario: OpenAI-compatible provider is selected
- **WHEN** an administrator selects the OpenAI-compatible GPT-5.5 option and its API base and key are configured server-side
- **THEN** subsequent LLM calls use the GPT-5.5 model and OpenAI-compatible endpoint

### Requirement: Settings API exposes selectable model configuration
The system SHALL expose available LLM model options and allow administrators to switch the active provider/model without returning API keys.

#### Scenario: User views API configuration
- **WHEN** an authenticated user opens Settings API configuration
- **THEN** the response includes model options, active provider/model, API base display value, and API key configured status
- **AND** the response does not include API key values

#### Scenario: Administrator switches active model
- **WHEN** an administrator saves a configured provider/model option
- **THEN** the system updates the active runtime LLM selection

#### Scenario: Non-admin switches active model
- **WHEN** a non-admin user attempts to update the active provider/model
- **THEN** the system rejects the request
