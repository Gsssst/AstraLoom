## Why

Paper AI reading shares are currently one-way notifications. Recipients can read the shared answer, but they cannot discuss, acknowledge, or mark follow-up directly inside the push center, so useful reading exchanges still leak into external chat tools.

## What Changes

- Add a discussion thread for each paper chat share notification.
- Let recipients and senders comment on a shared reading insight from the paper push center.
- Let users mark a share as useful, follow-up needed, or resolved.
- Notify relevant participants when a share receives a new comment.
- Keep the feature independent of project spaces so shares sent to arbitrary users work the same way as workspace-originated shares.

## Capabilities

### New Capabilities
- `paper-chat-share-discussion-threads`: Covers discussion comments and per-user collaboration status for paper AI reading shares.

### Modified Capabilities
- `paper-push-center-chat-share-feed`: Share cards expose lightweight discussion and status controls when expanded.
- `notification-digest-center`: Paper chat share discussion events create actionable in-app notifications.

## Impact

- Backend: add persistence for paper chat share threads/comments/statuses, migration, and notification endpoints.
- Frontend: update the paper push center share cards with discussion thread UI and status actions.
- Tests: add backend API tests and frontend contract tests for discussion controls.
