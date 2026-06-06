## Context

The chat page already uses a dedicated composer panel with prompt shortcuts, attachments, upload button, textarea, and send button. Most of the behavior is correct, but the visual treatment relies on flat icon buttons and generic spacing.

## Goals / Non-Goals

**Goals:**
- Make upload and send controls feel like first-class composer tools.
- Improve focus, hover, disabled, and attachment states.
- Keep the layout compact and work-focused.

**Non-Goals:**
- Redesign the entire chat page.
- Change upload semantics or add new file types.
- Change message rendering.

## Decisions

- Use CSS class-based styling for the composer instead of more inline styles.
  - Rationale: responsive and interaction states are easier to control in one place.

- Keep icon-first controls with tooltips.
  - Rationale: the composer is a repeated-use tool surface, and icons keep it dense without extra labels.

## Risks / Trade-offs

- Existing `home.css` has older chat composer rules -> mitigation: stronger, scoped rules in `responsive.css` target the active chat page classes.
