## Why

The chat assistant currently performs retrieval and Research Scout work behind the scenes, so users cannot see which tools were run, what they found, or which steps are waiting for confirmation. Phase 2 should make the assistant feel like a Codex/Claude Code style research worker with visible, structured tool execution rather than opaque prose.

## What Changes

- Add a chat tool execution trace payload for streamed responses.
- Define a safe tool registry for research workflows, starting with `search_papers`, `evaluate_papers`, `rank_recommendations`, and user-confirmed action placeholders such as `import_paper`.
- Emit trace steps during Research Scout runs: intent parsing, scholarly search, candidate evaluation, recommendation generation, and optional action availability.
- Render a compact tool trace panel in chat messages.
- Keep side-effecting tools as visible affordances that require user clicks; no automatic import or file mutation in this change.

## Capabilities

### New Capabilities
- `chat-tool-execution-trace`: Chat can stream and render structured tool execution steps for research workflows.

### Modified Capabilities
- `chat-research-scout-evaluation`: Research Scout exposes its internal search/evaluation/recommendation work as tool trace steps.

## Impact

- Backend: `backend/app/api/chat_sessions.py` stream metadata and Research Scout context construction.
- Frontend: `frontend/src/pages/ChatPage.tsx` message metadata types and trace rendering, plus scoped CSS.
- Tests: `frontend/tests/chat-research-scout-contract.test.mjs`.
- No database migration is required because traces are currently message metadata in the streamed response.
