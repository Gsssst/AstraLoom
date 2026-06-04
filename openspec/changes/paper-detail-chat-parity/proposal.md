## Why

The paper-detail AI assistant still uses an older isolated chat flow. It lacks the knowledge-base, web-enhancement, retrieval-depth, progress, and robust streaming controls that are now available in the main chat workspace.

## What Changes

- Keep the current paper content as the mandatory primary context for paper-detail questions.
- Add optional related-paper library retrieval, web enhancement, and retrieval depth controls.
- Auto-select deep retrieval when web enhancement is enabled.
- Reuse the backend mixed-retrieval strategy and robust JSON SSE events from the main chat flow.
- Add visible retrieval and generation progress text.
- Preserve related-paper references in paper chat messages and fix stale chat-history persistence.

## Capabilities

### New Capabilities
- `paper-detail-chat-parity`: Paper-detail AI Q&A provides main-chat retrieval controls and robust streamed responses while prioritizing the current paper.

### Modified Capabilities

## Impact

- Affects `backend/app/api/papers.py`, `frontend/src/pages/PaperDetailPage.tsx`, `frontend/src/styles/responsive.css`, and backend tests.
- No database migration or new dependency is required.
