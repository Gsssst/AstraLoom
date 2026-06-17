## Context

The shared `Markdown` component currently renders KaTeX output with global `.app-markdown .katex-display` overflow styles. The previous fix made long formulas scrollable, but setting the inner KaTeX box to `width/max-content` can interfere with KaTeX's display tag layout.

Paper chat references are already stored on assistant messages as `msg.references` with evidence ids such as `E1` and page metadata. The answer text often contains matching markers like `[E1]`, but the shared Markdown renderer treats them as plain text.

## Goals / Non-Goals

**Goals:**
- Preserve readable display formulas and keep equation numbers visually separated.
- Turn paper-chat evidence markers into clickable controls when matching reference metadata exists.
- Reuse existing PDF page navigation state and evidence drawer behavior.

**Non-Goals:**
- Add bounding-box level scrolling when bbox metadata is unavailable.
- Change backend evidence IDs or response shape.
- Add citation linking to non-paper chat pages in this change.

## Decisions

- Add a small `evidenceLinks` prop to the shared Markdown renderer. This keeps normal Markdown behavior unchanged and lets PaperDetailPage opt into evidence marker linking.
- Use a custom `text` renderer to split text nodes containing `[E<number>]` into buttons/chips. This avoids preprocessing the Markdown string and keeps citations inside paragraphs/lists.
- Restore KaTeX's internal display math layout by avoiding forced `width: max-content` on `.katex-display > .katex`; instead put horizontal scrolling on the display wrapper and style `.tag` separately.
- When a marker is clicked, set the PDF page to the evidence page and open the evidence reference group so users can inspect the source context.

## Risks / Trade-offs

- [Risk] Some evidence has no page number. -> Render it as a disabled-looking chip or plain marker with tooltip semantics; only page-backed markers navigate.
- [Risk] A marker could appear in code blocks. -> The custom text renderer only affects Markdown text nodes; code rendering remains handled by the code component.
- [Risk] Very long formulas still need horizontal scrolling. -> This is acceptable and avoids breaking equation tags.
