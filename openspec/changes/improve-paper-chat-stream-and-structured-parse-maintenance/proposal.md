## Why

Paper-detail AI answers can currently end with a visible "回答生成中途出现异常" block after already producing useful content, which pollutes the answer and makes users unsure whether to trust the response. Structured PDF parsing is also only exposed per paper, so administrators cannot repair or refresh many papers from the maintenance center.

## What Changes

- Treat late paper-chat stream interruptions as turn metadata/status instead of appending a large error paragraph into the answer content.
- Keep empty-answer and pre-content failures visible, so users still know when no usable answer was produced.
- Add a bounded maintenance-center action to batch reparse structured PDFs for papers that have PDFs or arXiv IDs.
- Show structured parse readiness and batch action controls in the paper library maintenance center.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-chat-turn-reliability`: Paper Q&A stream interruptions after visible content must not pollute the answer body.
- `paper-library-maintenance-center`: Administrators can run bounded structured PDF parse maintenance from the maintenance center.

## Impact

- Affects paper chat SSE event handling, paper detail chat UI state, maintenance APIs, maintenance center UI, and focused regression tests.
- No database migration; structured parse status remains derived from `Paper.metadata_json`.
