## Context

The app has an in-app notification table, unread badge, header popover, digest inbox, and workspace issue notifications. Workspace issue notification metadata already stores a target path, but the header popover only routes digest notifications and otherwise leaves issue notifications as read-only text.

## Goals / Non-Goals

**Goals:**
- Make workspace issue notifications visible as a first-class category in the global notification popover.
- Mark clicked notifications as read before navigating.
- Navigate workspace issue notifications to their metadata path so the workspace page opens the issue drawer through `?issue=<id>`.
- Allow lightweight category filtering from the notification list API for future inbox surfaces.
- Add a compact all-read control for the header notification list.

**Non-Goals:**
- Build a full notification inbox route.
- Add notification preferences, push transport, or email transport.
- Add database migrations or new notification categories beyond existing `workspace_issue`.
- Change digest inbox behavior or digest recommendation feedback.

## Decisions

- Use `metadata.path` as the canonical notification target for workspace issue events.
  - Rationale: workspace issue notifications already store durable workspace and issue identifiers plus a path, and the workspace page already supports `?issue=<id>`.
  - Alternative considered: recompute paths in the frontend from metadata. That duplicates backend knowledge and is less robust if routes change.

- Extend `/notifications/list` with an optional `category` query parameter.
  - Rationale: this keeps the header behavior unchanged while enabling scoped surfaces and tests for workspace issue notifications.
  - Alternative considered: create `/notifications/workspace-issues`. Too narrow for the general notification table.

- Add a generic `/notifications/read-all` endpoint with optional category support while preserving `/notifications/digests/read-all`.
  - Rationale: the header needs a simple all-visible read action, and digest-specific behavior remains stable.
  - Alternative considered: client loops through visible notifications. That creates unnecessary requests and races the unread badge.

- Keep the header popover compact rather than creating a new page.
  - Rationale: the current pain is the missing click-through loop, not long-term notification management.

## Risks / Trade-offs

- [Risk] Notification metadata may be missing `path` for older workspace issue rows.
  -> Mitigation: fall back to `/workspaces/<workspace_id>?issue=<issue_id>` when both identifiers exist.

- [Risk] The header popover can become crowded as notification categories grow.
  -> Mitigation: show concise labels and keep a future full inbox out of scope.

- [Risk] Mark-all-read could affect categories the user did not intend.
  -> Mitigation: implement optional category filtering and use the current header list scope for the popover action.
