## 1. OpenSpec And Design

- [x] 1.1 Create proposal, design, specs, and task list.
- [x] 1.2 Validate OpenSpec change before implementation.

## 2. Backend Persistence

- [x] 2.1 Add paper chat share thread, participant, comment, and per-user status models.
- [x] 2.2 Add migration and model exports.
- [x] 2.3 Add share-thread id generation to new paper chat share notifications while preserving legacy notifications.

## 3. Backend API

- [x] 3.1 Add endpoints to get a share thread, post comments, and update/clear current user's status.
- [x] 3.2 Enforce sender/recipient/participant authorization.
- [x] 3.3 Notify relevant participants when a new comment is posted.

## 4. Frontend Push Center

- [x] 4.1 Load thread data when a paper chat share card is expanded.
- [x] 4.2 Render comments, empty states, and post-comment composer inside expanded cards.
- [x] 4.3 Add useful, follow-up, resolved, and clear status controls.
- [x] 4.4 Route discussion notifications to the push center and target share.

## 5. Verification

- [x] 5.1 Add backend tests for authorization, comments, statuses, and notifications.
- [x] 5.2 Add frontend contract tests for discussion controls in expanded share cards.
- [x] 5.3 Run targeted backend/frontend tests, OpenSpec validation, and frontend build.
- [x] 5.4 Review diff and commit.
