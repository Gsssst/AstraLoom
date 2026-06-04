## Why

Chat retrieval controls currently expose knowledge-base search, web search, and response depth as independent toggles, but the depth selection is not sent to the backend and users have learned an unnecessary multi-step workaround to make web search useful. The system should coordinate these controls automatically and make mixed retrieval a first-class workflow.

## What Changes

- Add an explicit chat retrieval depth parameter to frontend requests and backend request validation.
- Automatically switch the frontend to deep retrieval when web enhancement is enabled.
- Keep knowledge-base retrieval enabled when web enhancement is selected, producing a combined retrieval context.
- Show the active retrieval strategy in the chat toolbar.
- Centralize backend retrieval-context construction for streaming and non-streaming chat.
- Reuse the existing web-search service with bounded timeout behavior.
- Add regression tests for retrieval limits and combined knowledge-base plus web context.

## Capabilities

### New Capabilities
- `chat-retrieval-mode-coordination`: Covers coordinated knowledge-base retrieval, web enhancement, depth selection, and mixed-context chat behavior.

### Modified Capabilities

None.

## Impact

- Affects chat toolbar state and request payloads in `frontend/src/pages/ChatPage.tsx`.
- Affects request validation and retrieval-context construction in `backend/app/api/chat_sessions.py`.
- Reuses and tightens `backend/app/services/web_search.py`.
- Adds focused backend regression tests.
