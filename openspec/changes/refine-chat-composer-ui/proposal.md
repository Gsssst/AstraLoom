## Why

The chat composer upload button and text input feel visually rough compared with the rest of the application. This makes the primary chat workflow feel less polished even though the underlying behavior works.

## What Changes

- Refine the chat composer panel, upload button, textarea, send button, prompt chips, and attachment chips.
- Keep existing upload, keyboard, and send behavior unchanged.
- Preserve responsive layout across desktop and mobile.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-workspace-visual-refinement`: Chat composer controls must present a polished, consistent input experience.

## Impact

- `frontend/src/pages/ChatPage.tsx`
- `frontend/src/styles/responsive.css`
