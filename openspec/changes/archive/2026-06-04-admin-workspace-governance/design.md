# Design

## Backend

Add `app/api/admin.py` with `/api/admin` endpoints protected by `require_admin`:

- `GET /overview`
  - users, active users, admin users, papers, project spaces, writing projects.
- `GET /users`
  - search by username/email/display name.
  - includes created time, active state, and role.
- `PATCH /users/{user_id}`
  - update role and active state.
  - disallow deactivating self.
  - disallow removing the last admin.
- `GET /workspaces`
  - lists project spaces with owner, status, role breakdown, and member count.

The service logic is intentionally direct and query-based. A future iteration can add persisted audit-log rows.

## Frontend

Add `AdminPage`:

- Overview cards.
- User management table with role select and active toggle.
- Workspace governance table.

Add admin-only navigation entry to `AppLayout`.

## Testing

Add backend regression tests for:

- Admin routes require `require_admin`.
- Last-admin/self-protection rules.
- Workspace role breakdown helper.

## Risks

- Without persisted audit logs, governance is visibility-first rather than forensic.
- Role updates only affect new JWTs after users refresh/re-login; APIs fetch the DB user on each request, so backend permission checks remain correct.
