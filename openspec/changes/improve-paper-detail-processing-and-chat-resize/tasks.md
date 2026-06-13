## 1. Backend Processing

- [x] 1.1 Add reusable processing enqueue metadata for queued papers.
- [x] 1.2 Submit direct BibTeX and Zotero imports to `process_paper_pipeline` immediately after commit.
- [x] 1.3 Sanitize PDF full text and structured metadata before database persistence.
- [x] 1.4 Roll back and continue reconciliation after one paper processing failure.

## 2. Detail Page Layout

- [x] 2.1 Add content/chat width state and resize handling when PDF is hidden.
- [x] 2.2 Render a desktop resize handle between content and AI Q&A panels in non-PDF mode.
- [x] 2.3 Keep mobile behavior unchanged.

## 3. Verification

- [x] 3.1 Add backend tests for queued processing and direct import enqueue behavior.
- [x] 3.2 Add backend tests for PDF sanitization and reconciliation rollback isolation.
- [x] 3.3 Add frontend contract coverage for non-PDF chat resizing.
- [x] 3.4 Run targeted backend tests, frontend contract tests, frontend build, and OpenSpec validation.
