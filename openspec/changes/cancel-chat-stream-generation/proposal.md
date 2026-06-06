## Why

GPT-compatible streamed replies can take noticeably longer than DeepSeek. Users need a clear way to stop a slow or mistaken generation without waiting for the request to finish or refreshing the page.

## What Changes

- Add a stop control while a chat message is streaming.
- Cancel the current browser stream request with `AbortController`.
- Preserve any already streamed assistant content and restore the composer to a send-ready state.
- Show a short cancelled status instead of treating user cancellation as a model failure.

## Capabilities

### New Capabilities
- `chat-stream-cancellation`: Chat users can stop the currently streaming assistant response.

### Modified Capabilities

## Impact

- Frontend streaming lifecycle in `frontend/src/pages/ChatPage.tsx`.
- Chat status styling in `frontend/src/styles/responsive.css`.
- Frontend regression coverage for the stop-generation control.
