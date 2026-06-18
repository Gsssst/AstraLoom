## Context

The push center now renders full shared paper chat content with Markdown, which is correct for reading a single share but too verbose for scanning a list. The existing app already uses explicit "展开/收起" controls in chat references and tool traces; the same pattern fits this page.

## Goals / Non-Goals

**Goals:**

- Default each `paper_chat_share` push card to collapsed.
- Show paper title, sender, date, message count, and a short selected-message preview while collapsed.
- Expand individual cards without affecting other cards.
- Continue rendering full content through `Markdown` when expanded.

**Non-Goals:**

- No persisted expansion state.
- No backend changes.
- No virtualized list or pagination changes.

## Decisions

1. **Track expanded card ids in local component state.**

   This avoids mutating notification metadata and keeps the behavior page-local.

2. **Collapsed preview uses existing excerpt/display/content fallback.**

   The collapsed state should stay compact, so it is allowed to use a short preview. Expanded state keeps the full-content-first Markdown rendering.

## Risks / Trade-offs

- [Risk] Users may miss that content is hidden. -> The action label includes message count and uses an icon.
