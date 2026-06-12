## Why

Paper Q&A and structured PDF parsing still fail in two important stable-use cases:

- Papers such as `Twilight: Adaptive Attention Sparsity with Hierarchical Top-$p$ Pruning` can have persisted `full_text` but an empty `pdf_path`. Manual structured parsing then fails even when the arXiv PDF already exists in the local cache.
- Table answers can still say that column names or table meaning are missing because retrieval passes isolated table rows or only four evidence snippets, instead of a complete table evidence package containing caption, table, page, and nearby explanatory text.

Related project patterns from RAGFlow, Docling, MinerU, and Marker point to the same fix: make parser state observable, recover and reuse cached PDFs, preserve structured Markdown/JSON-style table units, and retrieve grouped evidence rather than isolated text fragments.

## What Changes

- Recover missing `paper.pdf_path` from arXiv cache/download before structured parsing and paper Q&A evidence preparation.
- Return more actionable parse failure details to the UI instead of only showing a generic "PDF structured parsing failed" message.
- Add parser environment health reporting so administrators can see which parser backends are actually available.
- Replace fixed `top_k=4` paper Q&A evidence with an adaptive budget for table-like questions.
- Build table evidence packs that keep table blocks together with table captions and same-page context where available.
- Add regression coverage for the Twilight missing-`pdf_path` failure mode and table questions that need more than isolated rows.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Structured PDF parsing SHALL recover local PDF paths for arXiv papers when possible, and expose parser health/failure details.
- `paper-qa-evidence-grounding`: Paper Q&A SHALL use adaptive evidence budgets and grouped table evidence for table-like questions.

## Impact

- Affects structured PDF parse/reparse, maintenance status, paper Q&A context construction, current-paper evidence retrieval, Paper Detail parse error display, and focused regression tests.
- No database migration; recovered PDF paths and metadata use existing `Paper.pdf_path` and `Paper.metadata_json`.
