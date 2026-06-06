## 1. Backend Multimodal Path

- [x] 1.1 Add image attachment request models and validation for streaming chat.
- [x] 1.2 Build OpenAI-compatible multimodal user messages with text and image_url content parts.
- [x] 1.3 Add DeepSeek/text-only fallback context for image attachments.

## 2. Frontend Attachment Flow

- [x] 2.1 Preserve image data URIs from upload extraction.
- [x] 2.2 Send image attachments with chat stream requests while keeping PDF/text extracted context behavior.

## 3. Verification

- [x] 3.1 Add backend tests for GPT vision payloads and DeepSeek fallback.
- [x] 3.2 Validate the OpenSpec change.
- [x] 3.3 Run targeted backend/frontend checks and a real GPT image smoke test.
