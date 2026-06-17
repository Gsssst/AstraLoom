## Context

The paper detail page already passes a target PDF page into the shared `PDFViewer` when a user clicks an evidence marker. References often include a `snippet` and page number, but the PDF reader only scrolls to the page top. Mature PDF readers use either PDF.js find/text-layer indexing or precomputed annotation coordinates. For this first iteration, the project can get useful behavior without backend changes by searching the rendered PDF.js text layer.

## Goals / Non-Goals

**Goals:**
- Reuse existing `page + snippet` evidence metadata.
- Locate the best matching text-layer span after the target page is rendered.
- Highlight and scroll to that text, then clear the highlight automatically or on the next locator request.
- Fall back cleanly to page navigation if no reliable match is found.

**Non-Goals:**
- Persist PDF coordinates or annotation rectangles.
- Implement a full PDF.js find controller.
- Support native iframe PDF fallback with exact page-internal localization.

## Decisions

- Add an optional `targetLocator` prop to `PDFViewer`.
  - Rationale: page and snippet are both needed; keeping this in one prop avoids overloading `targetPage`.
  - Alternative considered: imperative refs. That would add more lifecycle coupling to the paper detail page.
- Search only inside the target page's `.react-pdf__Page__textContent` spans.
  - Rationale: the first iteration should stay scoped to the already rendered page and avoid parsing PDF internals.
  - Alternative considered: PDF.js `PDFFindController`. That is more robust but requires wiring deeper PDF viewer internals not currently used by `react-pdf`.
- Normalize whitespace and punctuation lightly before matching.
  - Rationale: PDF text layers often split line breaks and spaces differently from backend snippets.
  - Alternative considered: exact string matching. It would fail too often on wrapped text and hyphenation.

## Risks / Trade-offs

- Text-layer spans may split evidence across many nodes.
  - Mitigation: search concatenated span text and scroll to the first span overlapping the matched range.
- Formula/table/OCR snippets may not appear in the text layer.
  - Mitigation: preserve the existing page jump and show a fallback message instead of treating it as an error.
- The page may not have rendered when the locator request arrives.
  - Mitigation: retry briefly after page scroll/render before giving up.
