## Context

Paper digest inbox combines notification history, recommended papers, ingest actions, reading queue actions, and feedback. It currently surfaces most failures through endpoint-specific details or generic fallback strings. The shared `PageShell` and `getApiErrorDetails` are now available and suitable for this page.

## Goals / Non-Goals

**Goals:**
- Adopt `PageShell` with a clear title, subtitle, and back action.
- Keep the digest summary card and paper recommendation list intact.
- Provide persistent recovery details for failed digest actions.

**Non-Goals:**
- Change digest ranking, feedback semantics, or ingest behavior.
- Redesign individual paper cards.
- Add automatic retries.

## Decisions

- Use shell `actions` for “返回论文库”.
  - Rationale: returning to the parent module is a page-level action.
  - Alternative considered: keep the back button inside the body; rejected because it duplicates page header behavior.
- Use one `digestActionError` state for the latest failure.
  - Rationale: actions run one at a time and a single durable recovery panel avoids clutter.
  - Alternative considered: inline error for each digest/paper row; deferred because it would add complexity to a dense list.

## Risks / Trade-offs

- [Risk] Removing the gradient hero makes the page quieter.
  -> Mitigation: keep unread/digest count summary immediately below the shell header.
- [Risk] One error Alert can be overwritten by a later action.
  -> Mitigation: matches current toast behavior while adding persistence.
