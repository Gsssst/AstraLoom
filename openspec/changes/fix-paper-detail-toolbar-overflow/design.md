## Context

The paper detail toolbar is a horizontal flex row with the title on the left and multiple action groups on the right. The title currently has a fixed max width but its parent is not constrained with `min-width: 0`, while the action area does not have its own class or explicit shrink behavior. With long titles, flex sizing can push the right action groups into the viewport edge.

## Goals / Non-Goals

**Goals:**
- Keep the title to one line with ellipsis.
- Prevent status buttons, PDF controls, importance buttons, and favorite controls from being overlapped or clipped.
- Preserve the existing toolbar visual style and mobile wrap behavior.

**Non-Goals:**
- Redesigning the paper detail page header.
- Changing the semantics of reading status, importance, or favorite actions.

## Decisions

- Make `.paper-detail-toolbar-main` a flex item with `min-width: 0` and flexible growth.
- Make `.paper-detail-title` `flex: 1 1 auto` with `overflow: hidden` and a responsive max width.
- Add `.paper-detail-toolbar-actions` with `flex: 0 1 auto`, wrapping, and right alignment so actions remain visible under constrained width.

## Risks / Trade-offs

- Very narrow desktop widths may wrap action groups into a second toolbar line -> This is preferable to overlap or clipped controls.
