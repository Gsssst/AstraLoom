## Why

The paper detail PDF reader currently renders one page at a time and requires toolbar clicks to move between pages, which feels unlike normal PDF reading. The PDF and AI Q&A columns also use fixed proportions, making it hard to allocate space while reading or collapse the Q&A panel temporarily.

## What Changes

- Render enhanced PDF pages in a continuous vertical scroll flow.
- Keep the current page indicator synchronized with scroll position and support jumping to a target page.
- Preserve PDF text selection and page-aware quote capture in continuous mode.
- Add a desktop splitter between the PDF and AI Q&A panels so users can resize their relative widths.
- Allow dragging the splitter far right to collapse AI Q&A into a compact rail, with an explicit control to reopen it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: PDF reading and paper detail layout interactions are updated for continuous scrolling and resizable PDF/Q&A panels.

## Impact

- Affects `frontend/src/components/PDFViewer.tsx`, `frontend/src/pages/PaperDetailPage.tsx`, and responsive CSS.
- Adds or updates frontend tests/build verification.
- No backend API, database, or dependency changes.
