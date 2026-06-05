## Why

The paper detail workspace currently lets long AI responses increase the page height, which compresses the PDF reading area and makes it difficult to return to the original reading position. The page also embeds the PDF in a browser iframe even though the frontend already contains a `react-pdf` reader with a text layer, so selected PDF text cannot participate in the question workflow. Finally, paper chat retrieval ranks generic chunks only and does not recognize requests for named sections such as `Introduction`, which can produce incomplete or irrelevant context.

## What Changes

- Keep the PDF and paper AI chat panes bound to the available viewport height and make the chat message list scroll internally.
- Replace the paper detail iframe with the existing `react-pdf` reader and resize PDF pages to the panel width.
- Insert selected PDF text, including its page number, into the paper AI question composer automatically.
- Route questions that name common paper sections to matching section text before applying BM25 ranking, while preserving document-wide retrieval as a fallback.
- Add regression tests for section-aware retrieval and validate the frontend build.

## Capabilities

### New Capabilities

- `paper-reader-grounded-interaction`: Provides a stable split paper-reading workspace, section-aware paper question retrieval, and PDF selection-to-question interaction.

### Modified Capabilities

None.

## Impact

- Frontend: `PaperDetailPage`, reusable `PDFViewer`, and responsive layout styles.
- Backend: paper chunk retrieval and paper chat context assembly.
- Tests: focused backend retrieval tests.
- Dependencies and persistence: no new package, database migration, or external service.
