## 1. OpenSpec Validation

- [ ] 1.1 Validate the OpenSpec change before implementation.

## 2. Backend Data Model

- [ ] 2.1 Add workspace issue and issue comment ORM models with relationships.
- [ ] 2.2 Add Alembic migration for `project_space_issues` and `project_space_issue_comments`.
- [ ] 2.3 Include new tables in development database initialization and model exports.

## 3. Backend API and Service

- [ ] 3.1 Add workspace service methods for issue listing, creation, detail, update, and comments.
- [ ] 3.2 Enforce membership, viewer submission/comment permissions, and owner/editor triage permissions.
- [ ] 3.3 Record workspace activities for issue lifecycle events.
- [ ] 3.4 Add workspace API request/response schemas and routes under `/workspaces/{space_id}/issues`.

## 4. Frontend Workspace UI

- [ ] 4.1 Add issue state, loading, filters, create form, detail drawer, comments, and status actions to `WorkspaceDetailPage`.
- [ ] 4.2 Keep the issue section compact inside the workspace detail layout with open/closed counts and role-aware controls.
- [ ] 4.3 Preserve existing workspace assistant, resources, members, activity, and launchpad behavior.

## 5. Tests

- [ ] 5.1 Add backend tests for issue CRUD, filtering, comments, permissions, and activity recording.
- [ ] 5.2 Add frontend contract tests for issue list, filters, creation form, detail discussion, and role-aware triage controls.

## 6. Verification

- [ ] 6.1 Run OpenSpec strict validation after implementation.
- [ ] 6.2 Run targeted backend tests.
- [ ] 6.3 Run targeted frontend contract tests.
- [ ] 6.4 Run frontend build.
- [ ] 6.5 Run `git diff --check`.
