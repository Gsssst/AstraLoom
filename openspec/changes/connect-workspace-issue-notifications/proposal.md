## Why

Workspace issue events already create in-app notifications, but the header notification popover still treats most notifications as opaque text. Users need a clear loop from "someone commented/closed/reopened an Issue" to the exact workspace Issue discussion.

## What Changes

- Add category-aware notification listing/filtering support for workspace issue notifications.
- Make header notifications display user-friendly labels for digest, workspace issue, and system categories.
- When a user clicks a workspace issue notification, mark it read and navigate to the notification metadata path such as `/workspaces/<id>?issue=<id>`.
- Keep digest notification behavior unchanged, including navigation to the paper digest inbox.
- Add a compact "mark all visible/readable notifications read" control in the header popover.

## Capabilities

### New Capabilities

### Modified Capabilities

- `notification-digest-center`: Extend in-app notifications so workspace issue notifications are navigable from the global header and can be filtered/marked read without disrupting digest behavior.

## Impact

- Backend notification API list/read-all behavior and tests.
- Frontend app layout notification popover rendering, category labels, click navigation, and tests.
- No database schema change and no new frontend dependency.
