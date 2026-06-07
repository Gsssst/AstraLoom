## Context

Workspace detail is a project-space workbench containing linked resources, next actions, members, and activity. It currently duplicates a page header card after a standalone back button. The `PageShell` can own the page title, subtitle, back action, and module shortcuts while the existing content cards remain in place.

## Goals / Non-Goals

**Goals:**
- Use `PageShell` for workspace detail title/action layout.
- Preserve current resource and member workflows.
- Add persistent recovery guidance for workspace operation failures.

**Non-Goals:**
- Redesign workspace dashboard cards or launchpad content.
- Change workspace API calls or permissions.
- Adopt `PageShell` in the major research/paper/writing pages in this change.

## Decisions

- Use the loaded workspace name as the shell title, with a fallback while loading.
  - Rationale: the detail page identity is the selected workspace.
  - Alternative considered: keep a static “项目空间” title; rejected because detail pages should foreground the object name.
- Leave progress and role metadata in the first content card.
  - Rationale: those are object metrics, not page-level navigation.
- Use one `workspaceActionError` state.
  - Rationale: operations are sequential and the latest failure is most actionable.

## Risks / Trade-offs

- [Risk] The page may show a generic title while data loads.
  -> Mitigation: use a clear fallback and update as soon as `space` loads.
- [Risk] Moving module shortcuts to shell actions could crowd smaller screens.
  -> Mitigation: `PageShell` actions wrap on mobile.
