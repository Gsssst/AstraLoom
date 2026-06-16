## ADDED Requirements

### Requirement: Image generation tool is available
The runtime SHALL provide `generate_image` as a read-only registered chat tool for creating bounded research visual drafts.

#### Scenario: Registered image generation tool exposes schema
- **WHEN** the chat tool registry returns available tool schemas
- **THEN** the schema list includes `generate_image`
- **AND** the tool is marked as non-side-effect

#### Scenario: Execute image generation tool
- **WHEN** chat executes `generate_image` with a valid prompt and supported generation settings
- **THEN** the tool returns image artifacts in the observation
- **AND** the observation includes provider, model, size, style, and count metadata

#### Scenario: Image generation configuration failure is observable
- **WHEN** chat executes `generate_image` without a configured provider
- **THEN** the runtime returns a rejected observation
- **AND** the trace includes enough detail to diagnose missing configuration

#### Scenario: Deterministic routing handles explicit image prompts
- **WHEN** deterministic fallback receives an obvious image generation prompt
- **THEN** it emits a `generate_image` call with the user prompt as the generation prompt
