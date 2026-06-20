## Why

Paper chat shares now support discussion, but useful conclusions still stay inside the push center. Users need a durable way to turn selected AI reading shares and team comments into paper-level notes that can be found again while reading the paper.

## What Changes

- Add a paper chat share settlement action that appends a structured Markdown block to the current user's personal note for the shared paper.
- Include the original shared paper title, sender note, selected AI chat messages, comments, participant statuses, and timestamp in the saved block.
- Expose the action in the expanded paper chat share card in the paper push center.
- Preserve existing share-thread permissions: only share participants can save the discussion content, and shares without a local paper cannot be saved to paper notes.

## Capabilities

### New Capabilities
- `paper-chat-share-discussion-settlement`: Saving paper chat share discussions into durable paper notes.

### Modified Capabilities
- `paper-push-center-chat-share-feed`: Expanded share cards expose a settlement action without making the feed less scannable.

## Impact

- Backend: `backend/app/api/notifications.py`, paper user-note persistence through existing `UserPaper.personal_notes`.
- Frontend: `frontend/src/pages/PaperDigestInboxPage.tsx` share-card discussion actions and loading/success states.
- Tests: backend contract tests for authorization/content formatting and frontend contract tests for the new action.
