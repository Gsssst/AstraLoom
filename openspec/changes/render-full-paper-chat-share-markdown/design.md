## Context

The backend stores both bounded `excerpt` and fuller `content` for selected paper chat messages. The push center currently renders `excerpt || display_content || content` inside Ant Design `Paragraph`, so it uses the shortest field and bypasses the app's Markdown/KaTeX renderer. The shared answer can contain Markdown, formulas, tables, citations, and code blocks, so plain text is insufficient.

## Goals / Non-Goals

**Goals:**

- Use the app's existing `Markdown` component for shared message bodies.
- Prefer full `content`, then `display_content`, then `excerpt`.
- Keep cards readable without collapsing or truncating the answer.

**Non-Goals:**

- No backend metadata changes.
- No new Markdown renderer.
- No evidence link jump handling inside the push center in this slice.

## Decisions

1. **Reuse `Markdown`.**

   `Markdown` already normalizes math delimiters, renders GFM, and uses KaTeX. Reusing it keeps behavior consistent with paper AI chat.

2. **Choose full content first.**

   The push center is a detail surface, not a popover. It should show the content selected by the sender, while the bell notification popover can remain compact.

## Risks / Trade-offs

- [Risk] Very long answers increase card height. -> This is acceptable for the full push center; the source paper action remains available at the top.
