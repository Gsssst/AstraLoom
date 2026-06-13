## Why

Streaming chat currently forces the message list to scroll to the bottom whenever new content arrives. Users who scroll upward during generation are pulled back down repeatedly and cannot read earlier generated content.

## What Changes

- Preserve automatic bottom-following while the user is already near the bottom of a chat.
- Pause automatic scrolling when the user manually scrolls away from the bottom during generation.
- Resume automatic scrolling once the user scrolls back near the bottom.
- Apply the behavior to the main chat page and paper-detail AI Q&A.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `chat-workspace-visual-refinement`: main chat streaming scroll behavior must respect user manual scrolling.
- `paper-reader-grounded-interaction`: paper-detail AI Q&A streaming scroll behavior must respect user manual scrolling.

## Impact

- Affects frontend chat scrolling behavior in `ChatPage` and `PaperDetailPage`.
- Adds a small reusable frontend hook and contract coverage.
- No API, schema, dependency, or backend changes.
