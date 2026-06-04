## Context

Authentication exists and several personal features already use `get_current_user`, but authorization is inconsistent. Research projects can be created anonymously and listed globally, idea endpoints query records without checking project ownership, folders can be listed or deleted across users, usage history exposes cross-user records, and internal or global mutation endpoints are callable without an administrator check.

The data model already contains the ownership fields needed for research projects, folders, chat sessions, notifications, and personal paper state. This change therefore focuses on enforcing existing ownership boundaries rather than introducing migrations.

## Goals / Non-Goals

**Goals:**
- Use a reusable administrator dependency for system-wide operations.
- Require an authenticated owner for private research workspace and folder operations.
- Avoid leaking whether another user's private resource exists.
- Preserve public read-only paper discovery and explicit token-based research sharing.
- Align prominent frontend controls with the server-side administrator boundary.

**Non-Goals:**
- Migrating ownerless legacy projects or folders to a specific account.
- Adding team workspaces, project collaborators, or role management screens.
- Restricting public paper search, paper details, or token-based shared project views.
- Redesigning the full frontend layout.

## Decisions

### Centralize the administrator role check

Add `require_admin` in the security module as a FastAPI dependency layered on `get_current_user`. Routes that mutate the global paper library, submit internal tasks, or expose system-wide statistics use this dependency.

Alternative considered: repeat `user.role != "admin"` inside every endpoint. A dependency is easier to audit and prevents drift in status codes and messages.

### Resolve private research resources through owner-aware helpers

Add small helper queries in the research API for owned projects and owned ideas. Each helper filters by `current_user.id`; missing and foreign resources both return `404`.

Alternative considered: query by ID and then return `403` for foreign resources. Returning `404` reveals less information about private records and keeps resource lookup behavior simple.

### Treat shared views as a separate public capability

Only `GET /research/share/{token}` remains public. Creating or refreshing a share token requires project ownership. The shared payload stays read-only.

### Keep global paper reads public and protect global writes

Search, suggestions, details, citations, and Markdown export remain public. Ingestion, generated embeddings, generated global tags, forced full-text loading, batch global tags, imports, and permanent deletion require an administrator.

### Scope folder trees to the authenticated user

Folder listing filters roots by `user_id`. Creating a nested folder verifies the parent belongs to the same user. Deletion filters by both folder ID and `user_id`.

### Limit usage history by role

Ordinary users receive only their own history and cannot select another user. Administrators retain cross-user filters and global usage summaries. The system dashboard is administrator-only because it exposes all-user aggregates and recent chat titles.

## Risks / Trade-offs

- [Ownerless legacy private records become hidden] -> Keep them hidden by default and handle any ownership migration separately with an explicit administrative change.
- [Existing frontend controls may receive new `403` responses] -> Hide the primary global library controls for non-admin users while keeping backend enforcement authoritative.
- [A protected route may be missed during future development] -> Add route dependency regression tests and use the reusable dependencies for new system-wide endpoints.

## Migration Plan

1. Add the reusable administrator dependency.
2. Apply ownership checks to research and folder routes.
3. Apply administrator checks to cross-user statistics, dashboard, task, and global paper mutation routes.
4. Hide administrator-only paper-library controls for standard users.
5. Run regression tests and local smoke checks with standard and administrator accounts.

Rollback can revert the dependency additions without a database migration.

## Open Questions

- Ownerless legacy projects and folders need a separate migration decision if they must remain visible.
- Team collaboration should be modeled explicitly later rather than weakening owner checks.
