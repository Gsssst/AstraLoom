## Why

The chat page still leaves too much unused space below the composer and constrains conversation content too narrowly. Users need more vertical and horizontal reading space, especially when reviewing long Research Scout answers and candidate cards.

## What Changes

- Tighten the chat workspace viewport so the composer sits closer to the usable bottom edge.
- Reduce toolbar/message/composer padding that consumes vertical space.
- Widen the message and composer content rails so answers use more of the available desktop width.
- Keep mobile layout usable with smaller but still comfortable spacing.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-composer-bottom-alignment`: Composer alignment and chat workspace height are tightened to avoid large blank space below the input.
- `chat-workspace-visual-refinement`: Chat reading area uses more available width and vertical space without returning to a plastic/card-heavy style.

## Impact

- Frontend chat page layout classes and responsive CSS.
- Chat visual contract tests.
- No backend/API changes.
