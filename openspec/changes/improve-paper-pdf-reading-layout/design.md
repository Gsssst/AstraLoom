## Context

The current enhanced PDF reader uses `react-pdf` with a single `<Page>` bound to `pageNumber`. The paper detail desktop layout hides the content column when PDF is open and displays PDF plus AI Q&A as fixed-width panels. Mobile already uses tabbed panels and should remain unchanged.

Reference check:
- React-pdf examples render multiple pages by mapping `numPages` to repeated `<Page pageNumber={...} />` nodes under one `<Document>`.
- PDF.js viewer-style readers keep the page indicator synchronized with scroll position rather than forcing page-by-page buttons.

## Goals / Non-Goals

**Goals:**
- Make enhanced PDF reading feel like normal continuous PDF scrolling.
- Keep page-aware selection working when multiple pages are rendered.
- Allow desktop users to resize PDF and AI Q&A panel widths with a pointer drag.
- Collapse the AI Q&A panel when the splitter is dragged to the far right, while keeping a visible reopen control.

**Non-Goals:**
- Add virtualized PDF rendering.
- Rework native PDF fallback behavior.
- Change mobile panel navigation.
- Persist per-user panel widths server-side.

## Decisions

1. Render all pages for loaded PDFs in the enhanced reader.
   - Rationale: It directly matches the requested normal PDF reading behavior and is simple with `react-pdf`.
   - Alternative considered: render only nearby pages with virtualization. Rejected for this change because the current reader lacks virtualization infrastructure and correctness around text selection matters more.

2. Track each page wrapper with refs and infer the active page from scroll position.
   - Rationale: It keeps the toolbar page number useful without requiring explicit next/previous navigation.
   - Alternative considered: IntersectionObserver. Rejected for now because a scroll handler over page wrapper offsets is simpler and enough for bounded paper PDFs.

3. Use pointer events for the desktop splitter and keep width local to the page component.
   - Rationale: Pointer events work for mouse and trackpad drag without adding dependencies.
   - Alternative considered: CSS resize handles. Rejected because we need collapse thresholds and controlled width bounds.

## Risks / Trade-offs

- Rendering all pages can cost more memory for very long PDFs -> retain native fallback and keep page width bounded; future work can virtualize if needed.
- Page detection during fast scroll can lag slightly -> update on scroll and target-page navigation.
- Drag collapse may be discovered accidentally -> show a compact Q&A rail with a reopen button and retain the toolbar "hide PDF" control.
