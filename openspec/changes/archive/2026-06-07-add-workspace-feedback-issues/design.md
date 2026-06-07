## Context

Project spaces already have membership roles, durable resource links, activity recording, and a detail page that acts as the operational surface for a research project. User feedback needs a structured workflow similar to GitHub Issues: open/closed state, classification, labels, discussion, and filtering. GitHub Issues, GitLab Issues, and open-source trackers such as Plane all keep the first-class object simple while using labels/status/assignee fields to support triage.

## Goals / Non-Goals

**Goals:**
- Provide a workspace-scoped feedback issue tracker for bugs, ideas, questions, and tasks.
- Reuse workspace membership and editor permissions.
- Keep issue creation and triage visible inside the existing workspace detail page.
- Preserve a discussion trail through issue comments.
- Add activity records so issue work appears in workspace history.

**Non-Goals:**
- Build a full GitHub clone, kanban board, milestone system, or notification workflow in this change.
- Add public anonymous feedback intake.
- Add cross-workspace issue aggregation or admin moderation screens.
- Add external GitHub/GitLab synchronization.

## Decisions

- Store issues and comments in first-class tables.
  - Rationale: feedback issues need filtering, counts, comments, and auditability that do not fit cleanly in `ProjectSpaceActivity.metadata_json`.
  - Alternative considered: store issues in workspace metadata JSON. Rejected because it would make filtering, comments, and permission-safe updates fragile.

- Use `open` / `closed` as the initial status model.
  - Rationale: this matches the familiar GitHub Issues mental model and keeps triage simple.
  - Alternative considered: add `triaged`, `in_progress`, and `done` immediately. Deferred until the app needs workflow automation or a board.

- Use normalized string fields for `issue_type`, `priority`, and labels.
  - Rationale: it allows useful filtering without introducing a separate label-management UI.
  - Alternative considered: create label tables. Deferred because free-form labels are enough for the first version.

- Allow all workspace members to create and comment; require owner/editor to edit status, priority, labels, assignee, or issue metadata.
  - Rationale: feedback collection should be inclusive, while triage remains controlled by contributors who can edit workspace resources.
  - Alternative considered: only editors can create issues. Rejected because viewers should be able to report problems and requests.

- Render the frontend as a compact section on the workspace detail page.
  - Rationale: users asked for a place "in the project"; keeping issues near resources, assistant, and activities makes feedback actionable.
  - Alternative considered: create a separate route `/workspaces/:id/issues`. Deferred until issue volume or deep linking requires it.

## Risks / Trade-offs

- [Risk] The workspace detail page could become crowded.
  -> Mitigation: use a compact issue list with filters and a drawer/modal for creation and discussion.

- [Risk] Free-form labels can become inconsistent.
  -> Mitigation: provide common defaults in the UI and normalize label strings server-side.

- [Risk] Comments can be edited only by appending new comments in the first version.
  -> Mitigation: keep history append-only for now; add edit/delete moderation later if needed.

## Migration Plan

- Add Alembic migration `024_create_workspace_feedback_issues.py` with `project_space_issues` and `project_space_issue_comments`.
- Add ORM relationships and include tables in development `init_db`.
- Deploy migration before the updated backend starts handling issue routes.
- Rollback drops comments first, then issues.

## Open Questions

- Whether future versions should add project-level notifications when new feedback is submitted.
- Whether high-volume issue usage should move from an embedded workspace section to a dedicated route with saved filters.
