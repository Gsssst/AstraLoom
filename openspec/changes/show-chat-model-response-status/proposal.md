## Why

Users can switch between DeepSeek and the OpenAI-compatible GPT model, but the chat page does not clearly show which model is serving the current turn or whether the app is waiting for the first token. Slow GPT responses therefore look like a broken chat instead of a model latency issue.

## What Changes

- Expose safe stream metadata for the active provider, display label, model id, and supported capabilities.
- Show compact chat toolbar indicators for the active model, knowledge-base mode, web search mode, thinking support, and vision support.
- Show request lifecycle timing while a message is sending: retrieval/request start, waiting for first token, and streaming generation.
- Avoid exposing API keys, base URLs, or other secrets in chat stream metadata.

## Capabilities

### New Capabilities
- `chat-model-response-status`: Chat should make active model identity and response lifecycle visible during streamed replies.

### Modified Capabilities

## Impact

- Stream metadata contract in `backend/app/api/chat_sessions.py`.
- Chat response status handling and toolbar UI in `frontend/src/pages/ChatPage.tsx`.
- Frontend/backend regression tests for safe metadata and UI contract.
