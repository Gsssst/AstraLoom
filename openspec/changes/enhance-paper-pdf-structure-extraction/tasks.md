## 1. Structured PDF Extraction

- [x] 1.1 Add structured PDF extraction result types and metadata helpers.
- [x] 1.2 Extract page text, Markdown tables, captions, and visual placeholders with installed parsers.
- [x] 1.3 Persist bounded structured extraction metadata during full-text parsing.

## 2. Paper Q&A Retrieval

- [x] 2.1 Reuse cached structured metadata or lazily extract it from `pdf_path`.
- [x] 2.2 Include structured PDF blocks in paper evidence retrieval with source type and page numbers.
- [x] 2.3 Update prompt guidance so image placeholders are not treated as pixel-level analysis.

## 3. Verification

- [x] 3.1 Add unit tests for Markdown table conversion and structured block extraction.
- [x] 3.2 Add retrieval/context tests proving table and caption evidence enters paper Q&A.
- [x] 3.3 Run OpenSpec validation and targeted backend tests.
- [x] 3.4 Commit the change.
