## Why

The workspace AI assistant currently shows every context reference as visible tags in the assistant card, which can overflow the card and crowd the conversation. Assistant replies are also rendered as plain text, so Markdown answers lose structure and readability.

## What Changes

- Collapse workspace context references behind a compact toggle by default.
- Keep reference tags within the assistant card with ellipsis and wrapping constraints.
- Render assistant replies with the shared Markdown component while preserving plain text for user messages.
- Keep quick prompts, send behavior, and read-only assistant semantics unchanged.

## Capabilities

### New Capabilities

### Modified Capabilities

- `workspace-ai-assistant`: Refine the workspace assistant UI requirement to include collapsible context references, non-overflowing reference chips, and Markdown-rendered assistant messages.

## Impact

- `frontend/src/pages/WorkspaceDetailPage.tsx`
- Frontend contract tests for workspace assistant UI.
- No backend API, database, dependency, or environment changes.
