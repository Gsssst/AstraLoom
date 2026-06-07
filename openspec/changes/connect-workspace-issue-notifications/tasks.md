## 1. OpenSpec Validation

- [ ] 1.1 Validate the OpenSpec change before implementation.

## 2. Backend Notification API

- [ ] 2.1 Add optional category filtering to notification list API.
- [ ] 2.2 Add a generic read-all notifications endpoint with optional category scope.
- [ ] 2.3 Preserve digest-specific read-all behavior.

## 3. Frontend Header Notification Loop

- [ ] 3.1 Render readable category labels and colors for digest, workspace issue, and system notifications.
- [ ] 3.2 Navigate workspace issue notifications to metadata path or derived workspace issue deep link.
- [ ] 3.3 Add a header mark-all-read action that refreshes unread state and visible notifications.
- [ ] 3.4 Keep digest notification click-through to the paper digest inbox.

## 4. Tests

- [ ] 4.1 Add backend tests for category filtering and generic read-all behavior.
- [ ] 4.2 Add frontend contract tests for workspace issue notification routing, labels, and mark-all-read action.

## 5. Verification

- [ ] 5.1 Run OpenSpec strict validation after implementation.
- [ ] 5.2 Run targeted backend notification tests.
- [ ] 5.3 Run targeted frontend contract tests.
- [ ] 5.4 Run frontend build.
- [ ] 5.5 Run `git diff --check`.
