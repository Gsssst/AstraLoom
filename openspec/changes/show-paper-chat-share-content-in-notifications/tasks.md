## 1. OpenSpec And Contracts

- [x] 1.1 Create proposal, design, spec deltas, and task list.
- [x] 1.2 Update backend tests for all-user share resolution.
- [x] 1.3 Update frontend contract tests for notification preview and all-users action.

## 2. Backend Implementation

- [x] 2.1 Add `all_users` to paper chat share request schema.
- [x] 2.2 Resolve all active non-sender users when `all_users` is true.
- [x] 2.3 Keep explicit recipient and legacy workspace paths unchanged.

## 3. Frontend Implementation

- [x] 3.1 Add all-users share state and action in the paper chat share modal.
- [x] 3.2 Render rich `paper_chat_share` notification previews in the global popover.
- [x] 3.3 Keep explicit open-paper navigation and read marking from the preview.

## 4. Verification

- [x] 4.1 Run targeted backend/frontend contract tests.
- [x] 4.2 Run OpenSpec validation and frontend build.
- [x] 4.3 Review diff and commit.
