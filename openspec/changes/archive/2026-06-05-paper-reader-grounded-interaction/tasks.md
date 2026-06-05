## 1. Viewport-bound Paper Workspace

- [x] 1.1 Constrain the paper detail body and split panels to the available viewport height.
- [x] 1.2 Make the paper chat message list scroll internally while controls and composer stay fixed.

## 2. Section-aware Paper Retrieval

- [x] 2.1 Add section alias detection, heading normalization, and section extraction to the paper chunk service.
- [x] 2.2 Route paper chat context through section-aware retrieval with document-wide fallback.
- [x] 2.3 Add regression tests for named-section routing and fallback behavior.

## 3. PDF Selection-to-question Interaction

- [x] 3.1 Replace the paper detail iframe with the existing `react-pdf` viewer.
- [x] 3.2 Resize PDF pages from their panel width and pass selected text with its page number.
- [x] 3.3 Append selected PDF quotes to the paper question composer without dropping existing drafts.

## 4. Verification

- [x] 4.1 Run backend tests and frontend production build.
- [x] 4.2 Run strict OpenSpec validation for the change.

## 5. PDF.js Compatibility Hotfix

- [x] 5.1 Align the top-level `pdfjs-dist` dependency with the exact version used by `react-pdf`.
- [x] 5.2 Verify the Vite-transformed worker URL and rebuild the frontend.

## 6. Paper Composer Quote Card

- [x] 6.1 Store PDF selection separately from the editable question and render a removable quote card.
- [x] 6.2 Merge the quote into model context during send while keeping the visible user message compact.
- [x] 6.3 Replace the single-line paper question field with a bounded auto-growing multiline editor.

## 7. Grounded Paper Answer Reliability

- [x] 7.1 Parse downloaded paper PDFs with installed `pdfplumber` first and optional `fitz` fallback.
- [x] 7.2 Deduplicate concurrent paper full-text loads and let timed-out foreground waits finish in the background.
- [x] 7.3 Add a bounded paper thinking window that switches stalled reasoning to stable answer mode.
- [x] 7.4 Add regression tests for PDF parser fallback, shared loading, and thinking timeout recovery.
