## Context

The application header uses a fixed `48px` line height. The authenticated account entry currently places an avatar and `Typography.Text` inside a generic Ant Design `Space`, so the text inherits header typography behavior and does not have a stable visual container.

## Goals / Non-Goals

**Goals:**
- Keep the avatar and visible account name vertically centered in one horizontal control.
- Prevent long account names from changing header layout.
- Preserve the existing account menu and compact mobile presentation.

**Non-Goals:**
- Changing authentication state, user profile fields, or account menu actions.
- Redesigning unrelated header actions.

## Decisions

- Replace the generic account `Space` wrapper with a dedicated semantic `div` class so account layout is controlled explicitly rather than indirectly through inherited header styles.
- Give the wrapper an inline-flex layout, a compact rounded hover surface, and a normalized line height.
- Keep text truncation on the name and retain the existing mobile rule that hides the text below `768px`.

## Risks / Trade-offs

- [Risk] A wider account name could consume header action space on medium screens. → Mitigation: constrain the visible name width and apply ellipsis.
- [Risk] Styling the account entry could accidentally alter dropdown behavior. → Mitigation: preserve the existing `Dropdown` parent and click handler.
