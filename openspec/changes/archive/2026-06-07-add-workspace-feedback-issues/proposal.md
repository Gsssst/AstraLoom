## Why

Project spaces currently organize papers, research directions, writing drafts, members, and activities, but they do not provide a structured place to collect feedback, bugs, improvement requests, or follow-up tasks. A lightweight GitHub Issues-style surface would let workspace members capture and triage project feedback without scattering it across chat messages or activity logs.

## What Changes

- Add workspace-scoped feedback issues with title, description, status, type, priority, labels, creator, optional assignee, and timestamps.
- Add issue comments so members can discuss feedback without using the AI assistant conversation as a tracker.
- Add workspace APIs to list, create, view, update, close/reopen, and comment on issues while enforcing workspace membership and editor permissions.
- Add a compact Issues section to the project space detail page with filters, counts, issue creation, issue detail, comments, and status controls.
- Record workspace activity when issues are created, updated, commented on, closed, or reopened.

## Capabilities

### New Capabilities

- `workspace-feedback-issues`: Defines workspace-scoped feedback issue tracking, discussion, filtering, permissions, activity recording, and project-space UI.

### Modified Capabilities

## Impact

- Backend database models and Alembic migration for workspace issues and comments.
- Workspace API routes under `/api/workspaces/{space_id}/issues`.
- Workspace service permission checks, serialization, and activity recording.
- Project space detail frontend UI and API calls.
- Backend and frontend contract tests.
