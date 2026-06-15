## Why

The current chat experience is too generic for a research product: it can answer questions, but it does not guide users through finding interesting and useful papers as an explicit workflow. Inspired by GPT Researcher's planner/executor pattern, STORM's multi-perspective knowledge curation, and DocsGPT's document/tool-centered assistant model, chat should gain a task-specific "Research Scout" mode that turns paper discovery into a traceable, actionable conversation.

## What Changes

- Add a dedicated Research Scout mode to the chat UI so users can switch from generic Q&A to paper discovery.
- Extend chat requests with an assistant mode field while preserving the default generic chat behavior.
- In Research Scout mode, derive a compact discovery plan, use comprehensive scholarly search, and return structured paper candidates with "why interesting" and "why useful" rationales.
- Stream paper discovery status and structured candidate metadata back to the frontend so the user sees the assistant doing a research task rather than only producing prose.
- Surface candidate paper cards in chat with links, provider labels, years, abstracts, rationale, and next-action affordances for existing paper-library workflows.
- Keep first-stage scope focused on discovery and recommendation; Word/PPT/image generation/skill installation are future assistant tool modes.

## Capabilities

### New Capabilities
- `chat-research-scout-mode`: Chat can run an explicit paper-discovery mode that produces actionable scholarly candidates with transparent recommendation rationale.

### Modified Capabilities
- `chat-retrieval-mode-coordination`: Chat requests include an assistant mode while keeping knowledge-base, web, depth, and thinking controls coordinated.
- `paper-discovery-search-and-ingest`: Comprehensive scholarly discovery can be consumed from chat and represented as structured candidate metadata.

## Impact

- Frontend: `frontend/src/pages/ChatPage.tsx`, chat contract tests, and styles/classes used by the chat workbench.
- Backend: `backend/app/api/chat_sessions.py`, `backend/app/services/paper_search.py` consumers, and potentially small helper services for paper scouting.
- API: chat send/stream payloads gain an optional `assistant_mode`; stream metadata gains optional `research_scout` candidate payloads.
- No database migration is required for the first stage because candidates are returned as message metadata/references and actions reuse existing paper library routes.
