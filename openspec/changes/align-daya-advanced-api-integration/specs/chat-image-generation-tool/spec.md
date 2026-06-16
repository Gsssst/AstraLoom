## MODIFIED Requirements

### Requirement: Chat can generate bounded image artifacts
The system SHALL provide a backend image generation service that creates bounded image artifacts for chat tool observations. When the configured image provider is Daya-compatible, the service SHALL call the Vertex/Gemini-compatible `generateContent` API with image response modalities and parse returned image parts into data URLs.

#### Scenario: Generate image with configured provider
- **WHEN** the image generation service is called with a prompt, style, size, and count
- **THEN** it calls the configured provider with a bounded payload
- **AND** returns generated image artifacts as data URLs with provider/model metadata

#### Scenario: Generate image through Daya Vertex/Gemini API
- **WHEN** the image generation provider is configured for Daya-compatible Vertex/Gemini image generation
- **THEN** the service posts to `/v1beta/models/{model}:generateContent`
- **AND** the request includes `generationConfig.responseModalities` containing `TEXT` and `IMAGE`
- **AND** returned `inlineData` image parts are converted into `data:<mime>;base64,...` artifacts

#### Scenario: Missing provider configuration is rejected
- **WHEN** image generation is requested but no supported provider API key, base URL, or model is configured
- **THEN** the service rejects the request with a clear configuration error

#### Scenario: Provider response without image data is rejected
- **WHEN** the provider response does not include base64 image data or an image URL
- **THEN** the service rejects the request with a clear provider response error

#### Scenario: Image generation remains storage-free
- **WHEN** generated image artifacts are returned
- **THEN** the service does not persist them to the paper library, folders, projects, or local filesystem
