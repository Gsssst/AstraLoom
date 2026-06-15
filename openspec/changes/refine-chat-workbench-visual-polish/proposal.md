## Why

The current chat page works functionally, but the visual treatment feels too glossy and "plastic" compared with mature research/chat products. Before starting the next agent-tool phase, the chat workbench should establish a calmer, denser, more professional baseline that can carry tool traces and paper cards without looking decorative.

## What Changes

- Refine the chat toolbar, session rail, message stream, references, and composer into a quieter workbench layout.
- Reduce over-rounded surfaces, oversized shadows, and purple-heavy treatment in favor of neutral hierarchy with restrained accent colors.
- Make the session rail and composer feel like persistent product infrastructure rather than floating marketing cards.
- Improve message readability, action affordance placement, and reference strip styling without changing chat APIs or assistant behavior.
- Preserve existing chat functions: assistant mode, knowledge-base toggle, web toggle, depth selector, status popover, search, attachments, streaming, stop, session list, and Research Scout cards.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-workspace-visual-refinement`: Chat visual hierarchy and workbench polish are tightened to avoid decorative/plastic styling while preserving existing controls.
- `chat-composer-bottom-alignment`: Composer remains bottom-aligned while adopting a more restrained product-grade surface.

## Impact

- Frontend: `frontend/src/pages/ChatPage.tsx`, `frontend/src/styles/responsive.css`, and focused chat visual contract tests.
- OpenSpec: Adds a focused UI polish change under `openspec/changes/refine-chat-workbench-visual-polish/`.
- No backend/API/database changes are expected.
