## Why

Chat message actions such as "重新生成", "平衡", "创意", "精确", and "纯模型" set the input state and then call `handleSend()` through a timeout. Because React state updates are asynchronous, these actions can send stale text or fail to send the intended regeneration prompt.

## What Changes

- Allow the chat send handler to receive an explicit prompt override.
- Update assistant regeneration actions to send their intended prompt directly.
- Keep manual typing and Enter-to-send behavior unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-regenerate-actions`: Chat regeneration actions must send their intended prompt reliably.

## Impact

- Chat send and regeneration action handling in `frontend/src/pages/ChatPage.tsx`.
- Frontend regression coverage for explicit-prompt regeneration.
