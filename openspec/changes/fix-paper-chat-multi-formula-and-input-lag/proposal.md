## Why

Paper Q&A currently detects only one requested formula number. When the user asks "公式 8、9、10", retrieval only fetches formula 8, so the model correctly reports that formulas 9 and 10 are missing even though asking formula 9 or 10 alone works.

The paper chat input is also stored as top-level `PaperDetailPage` state. Every keystroke re-renders the full paper detail page, including PDF/chat-heavy subtrees, which can make typing lag visibly on long conversations.

## What Changes

- Detect multiple requested formula numbers from one question.
- Retrieve and pass evidence for each requested formula number before adding general document evidence.
- Keep single-formula behavior unchanged.
- Move paper chat composer text into a memoized local component so typing no longer re-renders the whole paper detail page.
- Preserve existing send, stop, upload, quote, attachment, and retry behavior.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Formula questions can request multiple numbered formulas in one turn.
- `paper-detail-chat-parity`: Paper chat composer typing remains responsive in heavy paper detail views.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`.
- Affects `frontend/src/pages/PaperDetailPage.tsx`.
- Adds focused backend tests.
- No database migration required.
