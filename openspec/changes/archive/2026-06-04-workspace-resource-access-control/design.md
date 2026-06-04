# Design: Workspace resource access control

## Access Model

Resource ownership does not move. Workspace membership grants additional access only when the resource is explicitly bound to the workspace.

Role behavior:

- `viewer`: can read linked resources.
- `editor`: can read and update linked resources.
- `owner`: can read and update linked resources.

Deletion remains resource-owner-only in this change.

## Resource Types

This change applies to:

- `research_projects`
- `writing_projects`

Papers are already broadly readable in the app, so they do not need extra read access in this iteration.

## Service Helper

`WorkspaceService.resource_role_for_user(...)` returns the strongest role a user has for a bound resource across all active spaces.

## API Integration

Research API:

- Project detail and read-oriented related endpoints use viewer access.
- Idea generation and mutable endpoints use editor access.
- Delete remains owner-only.

Writing API:

- Project detail uses viewer access.
- Project and section updates use editor access.
- Delete remains owner-only.
