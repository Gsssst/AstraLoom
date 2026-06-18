## Why

The paper digest center currently queries only daily digest notifications, so paper AI reading shares are visible in the bell popover but disappear from the dedicated "论文推送中心". Users expect that center to contain all paper-related pushes, including shared AI reading excerpts.

## What Changes

- Include `paper_chat_share` notifications in the paper digest center API, unread count, and mark-all-read behavior.
- Render paper AI reading share cards in `PaperDigestInboxPage` using selected-message metadata.
- Keep existing daily digest paper recommendation cards unchanged.

## Capabilities

### New Capabilities

- `paper-push-center-chat-share-feed`: Covers showing paper AI reading shares in the paper push center alongside daily digests.

### Modified Capabilities

- `notification-digest-center`: Digest center APIs and UI include paper chat share notifications as paper push items.

## Impact

- Backend API: update `/notifications/digests`, `/notifications/digests/unread-count`, and `/notifications/digests/read-all`.
- Frontend: update `PaperDigestInboxPage` to branch rendering by notification category.
- Tests: update contract coverage for mixed digest/share push center behavior.
