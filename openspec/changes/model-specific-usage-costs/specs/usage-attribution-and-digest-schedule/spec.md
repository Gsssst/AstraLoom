## ADDED Requirements

### Requirement: Usage costs are estimated with model-specific prices
The system SHALL estimate token usage cost using the recorded model's configured input-token and output-token prices.

#### Scenario: DeepSeek usage is recorded
- **WHEN** a usage record is logged for a DeepSeek model
- **THEN** the cost estimate uses the configured DeepSeek input and output token prices

#### Scenario: OpenAI-compatible usage is recorded
- **WHEN** a usage record is logged for the OpenAI-compatible GPT model
- **THEN** the cost estimate uses the configured OpenAI-compatible input and output token prices

#### Scenario: Unknown model usage is recorded
- **WHEN** a usage record is logged for a model without a matching price rule
- **THEN** the cost estimate uses the default fallback price and the usage record is still saved
