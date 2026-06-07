## Context

The Workspaces page currently duplicates a page hero with a gradient card, icon, title, subtitle, and primary action. The shared `PageShell` already provides those primitives in a restrained, reusable form.

## Goals / Non-Goals

**Goals:**
- Apply the shared shell to a list page with a primary action.
- Keep workspace card behavior and modal creation unchanged.
- Strengthen contract tests so future pages can follow the pattern.

**Non-Goals:**
- Redesign workspace cards or dashboard metrics.
- Change workspace create/edit/delete APIs.
- Adopt `PageShell` across all pages in this change.

## Decisions

- Use shell `actions` for the create-space button.
  - Rationale: primary page commands belong in a stable page action area.
  - Alternative considered: leave the button inside the list card; rejected because it would weaken the shell pattern.
- Preserve existing max width of 1180.
  - Rationale: this keeps the card grid width stable while changing only the page header.

## Risks / Trade-offs

- [Risk] The Workspaces page loses the visual emphasis of the gradient hero.
  -> Mitigation: workspace cards remain the primary content and the shell keeps a clear icon/title/action hierarchy.
- [Risk] Users may miss the create button after it moves.
  -> Mitigation: keep it as the only header action with the same icon and label.
