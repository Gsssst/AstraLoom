## 1. Evidence Locator

- [x] 1.1 Add a `PDFViewer` target locator that accepts page, snippet, and request id.
- [x] 1.2 Search the target page text layer with normalized snippet matching and retry while rendering catches up.
- [x] 1.3 Scroll to and temporarily highlight the matched text span.

## 2. Paper Chat Integration

- [x] 2.1 Pass evidence snippets from paper-chat references into the PDF locator when users click evidence markers.
- [x] 2.2 Preserve page-only fallback when no snippet or no match is available.

## 3. Verification

- [x] 3.1 Add frontend contract coverage for evidence snippet localization.
- [x] 3.2 Run targeted tests, frontend build, OpenSpec validation, and whitespace checks.
