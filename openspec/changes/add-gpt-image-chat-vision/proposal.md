## Why

The chat UI accepts image uploads, but the current send path only forwards the filename and a generic prompt to the LLM. Users expect GPT-compatible models with vision support to receive the actual image.

## What Changes

- Send uploaded images to the OpenAI-compatible GPT provider using Chat Completions multimodal `image_url` content parts.
- Keep DeepSeek/text-only providers on a clear fallback path that does not pretend the model can see the image.
- Preserve PDF/text upload behavior through extracted text context.
- Add tests for multimodal payload construction and text-only provider fallback.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-retrieval-mode-coordination`: Chat messages with image attachments must pass image content to GPT-compatible vision models and degrade clearly for text-only models.

## Impact

- Chat attachment request/response contract in `backend/app/api/chat_sessions.py`.
- LLM message typing and streaming calls in `backend/app/services/llm.py`.
- Chat composer upload/send flow in `frontend/src/pages/ChatPage.tsx`.
- Backend regression coverage for image attachment handling.
