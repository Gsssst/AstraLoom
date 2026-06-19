## 1. OpenSpec And Design

- [x] 1.1 Create proposal, design, specs, and task list.
- [x] 1.2 Validate OpenSpec change before implementation.

## 2. Backend Persistence

- [ ] 2.1 Add paper chat share thread, participant, comment, and per-user status models.
- [ ] 2.2 Add migration and model exports.
- [ ] 2.3 Add share-thread id generation to new paper chat share notifications while preserving legacy notifications.

## 3. Backend API

- [ ] 3.1 Add endpoints to get a share thread, post comments, and update/clear current user's status.
- [ ] 3.2 Enforce sender/recipient/participant authorization.
- [ ] 3.3 Notify relevant participants when a new comment is posted.

## 4. Frontend Push Center

- [ ] 4.1 Load thread data when a paper chat share card is expanded.
- [ ] 4.2 Render comments, empty states, and post-comment composer inside expanded cards.
- [ ] 4.3 Add useful, follow-up, resolved, and clear status controls.
- [ ] 4.4 Route discussion notifications to the push center and target share.

## 5. Verification

- [ ] 5.1 Add backend tests for authorization, comments, statuses, and notifications.
- [ ] 5.2 Add frontend contract tests for discussion controls in expanded share cards.
- [ ] 5.3 Run targeted backend/frontend tests, OpenSpec validation, and frontend build.
- [ ] 5.4 Review diff and commit.
