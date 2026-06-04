## Context

The application header is 48px tall. Desktop content uses 24px outer margins, while mobile content uses 12px outer margins. The chat workspace cancels the content padding with a negative margin, so its usable height must subtract the header and the two outer margins rather than a historical fixed 170px offset.

## Goals / Non-Goals

**Goals:**
- Fill the available chat viewport without leaving unused space below the composer.
- Keep the composer attached to the usable bottom edge on desktop and mobile layouts.

**Non-Goals:**
- Redesign the composer controls.
- Change application-wide content sizing or scrolling behavior.

## Decisions

- Use `calc(100vh - 96px)` for desktop: 48px header plus 24px top and bottom margins.
- Use `calc(100vh - 72px)` for mobile: 48px header plus 12px top and bottom margins.
- Keep the existing flex column layout so only the message list grows or shrinks while the composer remains visible.

## Risks / Trade-offs

- [Risk] Browser viewport behavior can vary on mobile devices with dynamic browser chrome. → Keep the change limited to the existing `100vh` strategy and adjust only the incorrect fixed offsets.
