## Context

The reader uses `react-pdf` and renders each page with a fixed calculated width. Global zoom would require re-rendering every page and can shift scroll position. A local magnifier can reuse the rendered page canvas and overlay a clipped, scaled copy of the current page near the cursor.

## Goals / Non-Goals

**Goals:**
- Let users inspect small PDF details from the current page without changing the page scale.
- Keep text selection and evidence highlighting usable.
- Keep the control lightweight and understandable.

**Non-Goals:**
- Add persistent full-document zoom controls.
- Support magnification in the browser-native PDF fallback iframe.
- Add image processing or backend PDF rendering.

## Decisions

- Implement a toggleable loupe rather than global zoom.
  - Rationale: this solves the "small local text" need while preserving current scroll/page state.
  - Alternative: change `Page` scale or width. That would reflow all rendered pages and can disrupt reading.
- Use CSS transforms on the existing `react-pdf__Page` content.
  - Rationale: no extra dependencies and works with the rendered canvas/text layers.
- Disable pointer events on the loupe overlay.
  - Rationale: pointer movement, scrolling, text selection, and evidence interactions remain controlled by the base PDF page.

## Risks / Trade-offs

- [Risk] The loupe shows a scaled copy of text layer overlays as well as canvas content. -> Mitigation: clip the copied page and keep it read-only with `pointer-events: none`.
- [Risk] Very small mobile screens may not have enough room for a large loupe. -> Mitigation: use responsive loupe dimensions in CSS.
