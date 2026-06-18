## Why

Paper AI reading share notifications currently only show a short title/content line and navigate to the paper page. Recipients need to inspect the shared question/answer excerpt directly in the notification center before deciding whether to open the paper.

## What Changes

- Expand paper chat share notifications in the global notification popover to render sender, paper title, note, and selected conversation messages.
- Add explicit actions in the notification card: open source paper and mark/read behavior remains intact.
- Add a share-modal shortcut to select all active users returned by the recipient search.
- Extend the share API with an `all_users` request flag so the backend can broadcast to all active users except the sender.

## Capabilities

### New Capabilities

- `paper-chat-share-notification-preview`: Covers rendering selected paper chat share content directly inside the notification center and selecting all recipients from the share modal.

### Modified Capabilities

- `notification-digest-center`: Paper chat share notifications become expandable/content-rich notification cards instead of only navigation rows.

## Impact

- Backend API: extend `POST /papers/{paper_id}/share-chat-insight` with `all_users`.
- Frontend: update `AppLayout` notification popover and `PaperDetailPage` share modal.
- Tests: update frontend notification/share contracts and backend share request coverage.
