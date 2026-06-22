## ADDED Requirements

### Requirement: Users manage their own model preference
The settings API SHALL let any authenticated user read, save, and test their own preferred LLM provider/model from the server-configured available options. Saving a user preference SHALL NOT mutate the process-wide runtime model default.

#### Scenario: User saves a preferred model
- **WHEN** an authenticated user saves a configured provider/model through `/settings/api-config`
- **THEN** the preference is persisted only for that user
- **AND** the response reports the user's selected provider/model
- **AND** the process-wide runtime model default is not changed

#### Scenario: User tests their preferred model
- **WHEN** an authenticated user runs the model connection test
- **THEN** the test uses that user's preferred provider/model when present
- **AND** the response does not expose API keys or raw API base secrets

#### Scenario: User has no preference
- **WHEN** an authenticated user has not saved a preferred provider/model
- **THEN** `/settings/api-config` reports the server default provider/model as the active selection
- **AND** the response indicates that the active selection comes from the server default

### Requirement: LLM calls resolve the current user's model preference
The LLM service SHALL resolve provider/model from the current authenticated request user's saved preference before falling back to the server default/runtime selection. Background tasks and unauthenticated contexts SHALL continue to use the server default/runtime selection.

#### Scenario: Two users choose different models
- **WHEN** user A saves an OpenAI-compatible model and user B saves a DeepSeek model
- **THEN** chat, paper Q&A, writing, and research LLM calls made by user A use the OpenAI-compatible model
- **AND** LLM calls made by user B use the DeepSeek model

#### Scenario: Background job calls the LLM
- **WHEN** a background job calls the LLM without an authenticated user context
- **THEN** the LLM call uses the server default/runtime model selection

### Requirement: Settings UI labels model selection as user scoped
The settings API tab SHALL present the model selector as the current user's model preference rather than a global administrator-only switch. The UI SHALL allow non-admin authenticated users to save and test a configured model option.

#### Scenario: Non-admin opens API settings
- **WHEN** a non-admin authenticated user opens the API settings tab
- **THEN** the save and test controls are enabled for configured model options
- **AND** the explanatory copy states that API keys remain server configured while model choice is personal
