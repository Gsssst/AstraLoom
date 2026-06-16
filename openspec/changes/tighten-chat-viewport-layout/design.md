## Context

The current chat workspace uses `height: calc(100vh - 96px)` and page-margin compensation from the surrounding shell, while the composer adds a border-top band and 12-14px padding. On wide desktop screenshots this makes the composer look high above the usable bottom and leaves the conversation area feeling undersized. Message rows and composer panels are capped at 1040px, which also underuses large displays.

## Goals / Non-Goals

**Goals:**
- Increase visible message area on desktop and mobile.
- Keep the composer close to the usable viewport bottom.
- Widen the message/composer rail on desktop.
- Preserve existing visual style and controls.

**Non-Goals:**
- Redesign chat interaction controls.
- Change Research Scout cards.
- Change backend streaming or retrieval behavior.

## Decisions

1. **Tighten layout in CSS first.**
   - Use chat-specific CSS variables for message rail width and page offsets.
   - Keep inline styles only where existing React code already needs dynamic behavior.

2. **Reduce vertical chrome.**
   - Toolbar padding and composer padding should be smaller.
   - Message list top/bottom padding should be reduced, with enough bottom breathing room for scrolling.

3. **Widen but cap content.**
   - Increase desktop max width from 1040px to a larger rail while keeping readable assistant bubbles capped.
   - User bubbles remain narrower than assistant content.

## Risks / Trade-offs

- **Too dense on mobile** -> Keep separate mobile padding rules.
- **Very wide assistant lines may hurt readability** -> Widen the row rail more than the bubble max width.
- **Header height variations** -> Use a more direct viewport calc and keep page-shell compensation scoped to chat.
