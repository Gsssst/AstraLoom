## Context

The app already has workspace issues, workspace activity, workspace AI assistant context, a notification table, an action-center service, and a global command palette. The next improvement should connect these existing systems rather than introducing a separate tracker product. GitHub Issues and Plane-style trackers both show the same pattern: issues become useful when they are linked to concrete project objects, searchable, visible in planning surfaces, and included in notifications.

## Goals / Non-Goals

**Goals:**
- Make workspace issues resource-aware and navigable from the objects they discuss.
- Keep the workspace detail page usable as features accumulate.
- Feed open high-priority issues into next actions and the action center.
- Notify relevant workspace members about issue lifecycle events.
- Let the workspace AI assistant reason over current open issues.
- Make issues searchable from the global command palette.

**Non-Goals:**
- Add external GitHub/GitLab sync.
- Add a kanban board, milestones, cycles, or sprint planning.
- Add full notification preference management for issue events.
- Add public anonymous issue submission.
- Add rich comment editing/deletion.

## Decisions

- Store issue resource references in `ProjectSpaceIssue.metadata_json`.
  - Rationale: this avoids a second migration for a flexible first version, and the issue table already has JSON metadata.
  - Alternative considered: create `project_space_issue_links`. Deferred until issues need multiple linked resources or analytics.

- Use URL query parameters for issue deep links.
  - Rationale: `/workspaces/:id?issue=<id>` works with the existing route and can open the drawer without adding a route file.
  - Alternative considered: `/workspaces/:id/issues/:issueId`. Deferred until the issue page needs a standalone route.

- Add workspace detail tabs locally in `WorkspaceDetailPage`.
  - Rationale: a lightweight tabbed layout solves crowding without splitting the page into many new route bundles.
  - Alternative considered: new route per section. Deferred until route-level bookmarking is needed for every section.

- Emit notifications directly from workspace issue service methods.
  - Rationale: issue lifecycle events already happen inside the workspace service, where member and actor context is available.
  - Alternative considered: event bus or background task. Too heavy for local in-app notifications.

- Search workspace issues from existing `/workspaces` payload.
  - Rationale: the command palette already fetches workspaces; including recent issue summaries keeps implementation small.
  - Alternative considered: add a dedicated issue search endpoint. Deferred until issue volume grows.

## Risks / Trade-offs

- [Risk] Adding issue summaries to workspace list could increase response size.
  -> Mitigation: include only a small, recent open issue summary with id, title, status, priority, and labels.

- [Risk] Resource-page issue creation needs a workspace target.
  -> Mitigation: reuse the workspace resource-link status endpoint to list spaces connected to the current resource, then allow choosing one.

- [Risk] Notifications can become noisy.
  -> Mitigation: notify workspace members except the actor, and keep all issue notifications in the existing in-app list.

- [Risk] Workspace detail page can still become dense.
  -> Mitigation: expose issues, resources, assistant, and activity behind tabs while keeping overview as the default.
