## 1. Backend Extraction Core

- [x] 1.1 Add `python-pptx` to backend dependencies while keeping the existing `python-docx` parser for Word files.
- [x] 1.2 Create a focused backend Office extraction helper that returns bounded structured text and metadata for `.docx` files.
- [x] 1.3 Extend the helper to return bounded per-slide structured text and metadata for `.pptx` files.
- [x] 1.4 Return clear unsupported-format errors for legacy `.doc` and `.ppt` files.

## 2. Chat Integration

- [x] 2.1 Wire the Office extraction helper into `/chat-sessions/extract-file`.
- [x] 2.2 Wire the same helper into the legacy `/{session_id}/upload` chat attachment path.
- [x] 2.3 Register read-only `extract_docx` and `extract_pptx` chat tools with planner-visible schemas.

## 3. Frontend Attachment Workflow

- [x] 3.1 Update the shared chat attachment picker to accept PDF, images, DOCX, DOC, PPTX, and PPT files.
- [x] 3.2 Keep frontend extraction error handling clear for unsupported legacy Office files.

## 4. Tests And Verification

- [x] 4.1 Add backend tests for DOCX paragraph/heading/table extraction.
- [x] 4.2 Add backend tests for PPTX slide/title/text extraction.
- [x] 4.3 Add backend tests for unsupported `.doc` and `.ppt` guidance.
- [x] 4.4 Update frontend attachment contract tests for the accepted file list.
- [x] 4.5 Run OpenSpec validation, focused backend tests, frontend contract tests, and frontend build.
