## Why

Paper chat share cards in the paper push center currently show truncated excerpts as plain text. Long answers cannot be fully inspected, Markdown formatting is lost, and formulas are not rendered.

## What Changes

- Render paper chat share message content with the shared Markdown component instead of plain `Paragraph`.
- Prefer full `content` over bounded `excerpt` for paper push center cards.
- Preserve question/answer labels while allowing Markdown, tables, code blocks, and KaTeX formulas in the shared answer body.

## Capabilities

### New Capabilities

- `paper-chat-share-markdown-rendering`: Covers full Markdown/LaTeX rendering of shared paper chat messages in the paper push center.

### Modified Capabilities

- `paper-push-center-chat-share-feed`: Paper chat share cards display complete message content rather than excerpt-only text.

## Impact

- Frontend: update `PaperDigestInboxPage` paper chat share rendering.
- Tests: update frontend contract coverage for Markdown rendering and full-content preference.
