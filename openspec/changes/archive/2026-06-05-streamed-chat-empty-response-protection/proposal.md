## Why

Reasoning-capable models can occasionally finish a streamed request without emitting visible answer text. The chat backend currently persists that empty result as a successful assistant message, while the frontend stream parser can also lose partial SSE frames split across network chunks.

## What Changes

- Retry streamed LLM calls that finish without visible content, including reasoning-only responses.
- Prevent empty assistant messages from being persisted by returning a visible retryable fallback.
- Encode chat-session SSE payloads as JSON events so multiline model output is preserved.
- Buffer partial SSE frames in the chat frontend instead of parsing each network chunk independently.
- Display a concise progress label while retrieval and generation are running.
- Add regression tests for reasoning-only retries, empty-response fallbacks, and SSE encoding.

## Capabilities

### New Capabilities
- `streamed-chat-empty-response-protection`: Streamed chat requests preserve visible content, expose progress, and never save a blank assistant reply.

### Modified Capabilities

## Impact

- Affects `backend/app/services/llm.py`, `backend/app/api/chat_sessions.py`, `frontend/src/pages/ChatPage.tsx`, and backend tests.
- The chat-session SSE endpoint uses JSON event payloads; the chat frontend is updated in the same change.
