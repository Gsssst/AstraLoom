## Why

Research Scout currently regresses into ordinary web-augmented chat for paper-finding prompts: it can show unrelated generic web sources, omit candidate cards/actions, and lose previously fixed stream-scroll behavior. This makes the paper scout unreliable exactly when users expect structured scholarly discovery.

## What Changes

- Auto-route paper-search style prompts to Research Scout even when the user forgets to switch modes.
- In Research Scout mode, bypass ordinary generic web retrieval and show only scholarly candidate references.
- Make venue/year constraints visible in intent parsing and candidate constraint matching so conference requests do not look ignored.
- Keep source strips limited to retrieved/used scholarly candidates in Research Scout, with labels that do not imply generic web citations.
- Re-harden streaming auto-scroll so user upward scrolling is not overridden while long answers stream.
- Add contract tests for Research Scout routing, source isolation, candidate card payloads, evaluation metadata, and scroll behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `chat-retrieval-mode-coordination`: Paper-search prompts must route to Research Scout and avoid generic web retrieval in scout mode.
- `chat-web-research`: Displayed web sources must represent relevant retrieval context and must not appear for Research Scout scholarly discovery.
- `chat-research-scout-evaluation`: Research Scout responses must expose candidate cards, actions, and evaluation metadata for paper-finding prompts.
- `chat-workspace-visual-refinement`: Streaming chat must preserve user-controlled scroll position during generation.

## Impact

- Backend: `backend/app/api/chat_sessions.py`, possibly `backend/app/services/web_search.py`.
- Frontend: `frontend/src/pages/ChatPage.tsx`, `frontend/src/hooks/useChatAutoScroll.ts`.
- Tests: frontend contract tests and focused backend syntax/contract checks.
- No database migration or dependency change.
