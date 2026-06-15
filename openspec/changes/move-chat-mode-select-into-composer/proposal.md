## Why

The assistant mode selector controls how the next message is sent, so it belongs near the composer instead of competing with global toolbar controls. Moving it into the existing composer mode chip makes mode switching more contextual and reduces toolbar clutter.

## What Changes

- Move the assistant mode selector from the top toolbar into the composer mode area.
- Preserve the existing `general` and `research_scout` behavior, including auto-enabling deep web search for Research Scout.
- Keep the toolbar focused on session title, model/status, retrieval controls, search, and overflow actions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-workspace-visual-refinement`: Assistant mode switching is presented as part of the composer interaction surface rather than the top toolbar.

## Impact

- Frontend: `frontend/src/pages/ChatPage.tsx`, `frontend/src/styles/responsive.css`, and focused chat contract tests.
- No backend/API/database changes.
