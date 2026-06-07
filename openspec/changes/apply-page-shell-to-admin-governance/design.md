## Context

The Admin page is an operational dashboard for users, workspace governance, and activity. It is not a landing/hero page, so the shared `PageShell` is a better fit for its title, subtitle, and refresh command. The page also uses generic `message.error` calls, while the shared error helper can provide recovery guidance.

## Goals / Non-Goals

**Goals:**
- Adopt `PageShell` for Admin page structure.
- Preserve all current admin tables, cards, filters, and activity timeline.
- Persist structured error recovery details for failed admin operations.

**Non-Goals:**
- Change admin API behavior or authorization rules.
- Redesign table columns or governance metrics.
- Add new admin actions.

## Decisions

- Keep the non-admin warning outside the shell.
  - Rationale: unauthorized access is an exception state, not the normal admin workspace.
  - Alternative considered: wrap warning in shell; deferred because it adds little value.
- Use one `adminActionError` state.
  - Rationale: admin operations are sequential and the latest failure is the most useful recovery target.

## Risks / Trade-offs

- [Risk] Removing the gradient hero reduces visual distinction of admin mode.
  -> Mitigation: keep `SafetyCertificateOutlined` in the shell icon and preserve governance metric cards.
- [Risk] Persistent errors can clutter the dashboard.
  -> Mitigation: make the Alert dismissible and clear it on successful data/user operations.
