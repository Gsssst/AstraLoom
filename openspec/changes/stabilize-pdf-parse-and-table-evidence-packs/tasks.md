## 1. PDF Path Recovery And Parser Diagnostics

- [x] 1.1 Add a reusable arXiv PDF path resolver that restores and persists `paper.pdf_path` when missing.
- [x] 1.2 Use the resolver in forced structured reparse, lazy structured parse, and paper Q&A evidence preparation.
- [x] 1.3 Preserve actionable parse failure status when PDF recovery or parsing fails.
- [x] 1.4 Add parser health metadata/API fields for configured backend and available parser capabilities.
- [x] 1.5 Improve Paper Detail parse failure display to show concrete backend error details.

## 2. Table Evidence Packs

- [x] 2.1 Add adaptive current-paper evidence budget for table-like questions.
- [x] 2.2 Build grouped table evidence packs with table, same-page table caption, and same-page text context.
- [x] 2.3 Keep grouped evidence references page-aware and preserve parser source, score, snippet, and metadata.
- [x] 2.4 Avoid unbounded prompt growth through per-pack and total evidence caps.

## 3. Verification

- [x] 3.1 Add regression tests for Twilight-style full-text-without-pdf-path structured reparse.
- [x] 3.2 Add tests for parser health reporting.
- [x] 3.3 Add tests for table evidence packs and adaptive evidence budgets.
- [x] 3.4 Run OpenSpec validation, targeted backend tests, frontend build, and diff checks.
- [x] 3.5 Commit the change.
