## Why

Paper-detail AI Q&A can fall back to an empty-response warning after a reasoning-heavy model call, even though the main chat remains usable. Thinking output is also held in one page-level panel, so separate turns appear merged together, and paper Q&A has no visible way to remove its saved conversation history.

## What Changes

- Add a paper-answer recovery path that retries a reasoning-only or empty paper response with an explicit concise-answer prompt before showing the final warning.
- Bind reasoning text and streaming state to the assistant message for each turn in both main chat and paper-detail Q&A.
- Persist paper-detail reasoning with its corresponding saved history message.
- Add an authenticated paper-detail control to clear saved Q&A history.
- Add regression tests for paper-answer recovery and history clearing behavior.

## Capabilities

### New Capabilities
- `paper-chat-turn-reliability`: Covers visible-answer recovery, per-turn reasoning display, and deletion of saved paper-chat history.

### Modified Capabilities

## Impact

- Affects paper Q&A streaming and history endpoints in `backend/app/api/papers.py`.
- Affects per-turn stream rendering in `frontend/src/pages/ChatPage.tsx` and `frontend/src/pages/PaperDetailPage.tsx`.
- Extends the ephemeral main-chat message shape in `frontend/src/stores/useChatSessionStore.ts`.
- Adds focused backend regression coverage without introducing a schema migration.
