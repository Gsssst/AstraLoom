## Why

The chat workspace is functional but visually fragmented: destructive actions compete with primary controls, session items are spacious and noisy, and the empty state and composer feel disconnected. Refining the hierarchy will make the workspace calmer, easier to scan, and more intentional without changing its behavior.

## What Changes

- Consolidate the chat toolbar into a clear title area and a compact group of consistent controls.
- Move the destructive clear-chat action into a secondary overflow menu with confirmation.
- Reduce conversation sidebar width and density, soften selected state, show timestamps, and reveal delete controls on hover.
- Improve the empty state hierarchy with a stronger brand treatment and clearer first-step guidance.
- Restyle the composer as a lighter floating interaction area with consistent prompt chips and controls.
- Preserve mobile drawer behavior and existing chat APIs.

## Capabilities

### New Capabilities
- `chat-workspace-visual-refinement`: Covers visual hierarchy, compact session browsing, safe secondary actions, and a cohesive chat composer.

### Modified Capabilities

None.

## Impact

- Frontend-only change.
- Primarily affects `frontend/src/pages/ChatPage.tsx` and `frontend/src/styles/responsive.css`.
- No backend API, dependency, or data model changes.
