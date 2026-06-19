## Why

Paper AI reading share cards can contain long Markdown answers. Showing every share fully expanded makes the paper push center hard to scan when multiple people share reading notes.

## What Changes

- Make paper chat share cards in the paper push center collapsed by default.
- Show compact metadata and a short preview while collapsed.
- Add an explicit expand/collapse action per share card.
- Preserve full Markdown/LaTeX rendering when expanded.

## Capabilities

### New Capabilities

- `paper-chat-share-card-collapse`: Covers collapsed-by-default paper chat share cards and per-card expansion.

### Modified Capabilities

- `paper-push-center-chat-share-feed`: Share cards become scannable summary rows until expanded.

## Impact

- Frontend: update `PaperDigestInboxPage` state and paper chat share card rendering.
- Tests: update frontend contract coverage.
