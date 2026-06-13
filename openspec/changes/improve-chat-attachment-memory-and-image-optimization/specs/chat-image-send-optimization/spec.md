## ADDED Requirements

### Requirement: Chat image payloads are optimized before model submission
The system SHALL optimize uploaded image attachments before sending them to the model while still accepting source image files up to the configured 50MB upload limit.

#### Scenario: User uploads a large image
- **WHEN** a user uploads a supported image file no larger than 50MB
- **THEN** the chat surface extracts the image and prepares a bounded model-ready image payload

#### Scenario: Optimized image is sent
- **WHEN** the user sends a question with an optimized image attachment
- **THEN** the request uses the optimized image data URL and includes the original filename and MIME type metadata

#### Scenario: Image optimization fails
- **WHEN** browser-side image optimization fails for a supported image
- **THEN** the chat surface falls back to the extracted image data URL and does not block sending

#### Scenario: User sees optimization status
- **WHEN** an image attachment is optimized or falls back to the original payload
- **THEN** the attachment chip shows a concise status indicating whether it is optimized or using the original payload
