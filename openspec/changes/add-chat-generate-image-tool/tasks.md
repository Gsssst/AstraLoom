## 1. Image Generation Service

- [ ] 1.1 Add image generation provider/model configuration fields.
- [ ] 1.2 Create a backend image generation service with bounded args and provider configuration checks.
- [ ] 1.3 Implement OpenAI-compatible `/images/generations` request and response parsing for base64/url image data.
- [ ] 1.4 Return clear errors for missing configuration and malformed provider responses.

## 2. Chat Tool Runtime Integration

- [ ] 2.1 Add `GenerateImageArgs` and register read-only `generate_image` in the default chat tool registry.
- [ ] 2.2 Package generated images as `ChatToolObservation` artifacts, references, context, and details.
- [ ] 2.3 Add deterministic fallback routing for explicit image-generation prompts.

## 3. Tests And Verification

- [ ] 3.1 Add backend tests for image generation payload construction and response parsing.
- [ ] 3.2 Add backend tests for missing configuration and malformed provider responses.
- [ ] 3.3 Add backend tests for `generate_image` schema, successful observation, rejected observation, and deterministic routing.
- [ ] 3.4 Run OpenSpec validation and focused backend tests.
