# admin-workspace-governance

## Why

The product now supports multiple users and project spaces, but administrators do not have a dedicated control surface to inspect users, adjust roles, disable accounts, or review project-space ownership. This makes P9 incomplete from an operational perspective.

## What Changes

- Add admin-only APIs for system overview, user management, and workspace governance.
- Allow administrators to list users and update roles / active status safely.
- Show project spaces with owner and member counts for governance.
- Add a frontend admin console visible only to admin users.
- Keep regular users out of admin navigation and API access.

## Non-Goals

- Full audit-log persistence table.
- Fine-grained per-resource permission editing.
- Enterprise SSO / organization management.
- Real-time collaboration controls.

## Reference Patterns

- RBAC-first admin dashboards expose user role and activation controls separately from normal profile settings.
- Workspace products separate user membership roles from global administrator privileges.
- Operational dashboards provide counts, recent risk indicators, and resource ownership visibility before deeper workflow actions.

## Success Criteria

- Non-admin users cannot access admin APIs.
- Admins can view system counts and user list.
- Admins can promote/demote users and activate/deactivate accounts with self-protection rules.
- Admins can inspect project spaces, owners, roles, and member counts.
- Frontend exposes a clear admin console for admin users.
