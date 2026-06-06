## ADDED Requirements

### Requirement: Image attachments reach GPT-compatible vision chat
The system SHALL send uploaded image content to the OpenAI-compatible GPT provider using Chat Completions multimodal content parts.

#### Scenario: GPT-compatible provider receives an image attachment
- **WHEN** a user sends a chat message with an image attachment while the active provider is OpenAI-compatible
- **THEN** the LLM request includes the user's text and the image data URI in the same user message

#### Scenario: Text-only provider receives an image attachment
- **WHEN** a user sends a chat message with an image attachment while the active provider is DeepSeek
- **THEN** the system does not send the image bytes and tells the model that visual image content is unavailable for the selected model

#### Scenario: PDF and text attachments are sent
- **WHEN** a user sends PDF or text attachments
- **THEN** the system continues to send extracted text as context without requiring vision support
