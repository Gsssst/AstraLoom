## Why

Paper-detail Q&A currently treats every answer as needing three evidence references for full coverage. This mislabels targeted section questions such as "请拆解第 3.2 节" as only 33% covered when the backend correctly retrieved one large exact section range.

## What Changes

- Add section-targeted evidence metadata to paper chat responses when retrieval matches a requested numbered section.
- Mark exact numbered-section hits as sufficient even when the answer has only one current-paper evidence reference.
- Update frontend evidence confidence scoring and labels to show "章节命中" for exact section hits instead of "部分支撑".
- Preserve existing evidence-count behavior for broad, table, visual, and document-wide questions.
- Add backend and frontend tests for section-specific evidence confidence.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-qa-evidence-grounding`: Current-paper evidence metadata distinguishes exact targeted section hits from generic top-k evidence count.
- `paper-detail-chat-parity`: Paper-detail chat UI uses targeted section metadata consistently for streamed and non-streamed answers.

## Impact

- Affects paper chat evidence metadata in `backend/app/api/papers.py`.
- Affects frontend evidence confidence scoring and labels in `frontend/src/services/researchAlgorithms.ts` and `frontend/src/pages/PaperDetailPage.tsx`.
- Adds focused backend and frontend tests.
- No database migration or new dependency is required.
