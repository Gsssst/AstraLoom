## Why

The desktop chat workspace uses an outdated viewport-height subtraction, leaving an unnecessary blank area below the message composer. The chat surface should use the available page height so the composer visually anchors to the bottom edge.

## What Changes

- Recalculate the chat workspace height from the actual application header and page margins.
- Use separate desktop and mobile height calculations because their page margins differ.
- Preserve the current composer padding while removing the unused space below it.

## Capabilities

### New Capabilities
- `chat-composer-bottom-alignment`: The chat workspace fills the available viewport and keeps the composer aligned to the usable bottom edge across desktop and mobile layouts.

### Modified Capabilities

## Impact

- Affects `frontend/src/styles/responsive.css`.
- No API, data model, or dependency changes.
