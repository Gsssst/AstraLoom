## Why

The Research Scout agent trace is useful for debugging, but it consumes too much vertical space in normal reading. Users should see a compact summary by default and expand the full tool sequence only when needed.

## What Changes

- Make chat tool execution traces collapsed by default.
- Show a one-line trace summary with workflow, stop reason, step count, and latest meaningful status.
- Add an explicit expand/collapse control for the full tool step list.
- Preserve all existing trace metadata and Research Scout cards.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-workspace-visual-refinement`: Tool execution traces default to a compact collapsed state with user-controlled expansion.

## Impact

- Frontend chat page rendering in `frontend/src/pages/ChatPage.tsx`.
- Scoped chat trace CSS in `frontend/src/styles/responsive.css`.
- Frontend contract tests for Research Scout trace behavior.
