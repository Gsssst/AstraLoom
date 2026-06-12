## Why

Paper Q&A still cannot reliably answer exact table-value questions when the PDF parser extracts merged, garbled, or generic-column tables. Increasing retrieval breadth does not fix this because the evidence itself is already damaged before it reaches the model.

GitHub references point to the required direction: Marker provides table-specific conversion and optional LLM correction with JSON/cell geometry, MinerU can output table HTML/JSON and handle scanned/garbled PDFs with OCR, Docling preserves table structure in advanced document exports, and RAGFlow treats parser choice and visible document chunks as part of retrieval quality.

## What Changes

- Add a high-fidelity table extraction path that can be invoked after normal structured parsing.
- Support a configurable external table parser command so deployments can use Marker, MinerU, Docling table export, or another table-specialized parser without hard-coding one dependency.
- Preserve table cell structure alongside Markdown: headers, rows/cells, source parser, confidence, page, caption, and quality flags.
- Detect low-quality tables more aggressively, including merged numeric cells, inconsistent row widths, generic headers, empty cells, and malformed Markdown.
- Automatically attempt high-fidelity table repair when normal parsing produces low-quality tables.
- Add maintenance-center support for a low-quality table repair queue and a bounded repair action.
- Make paper Q&A prefer repaired structured table cells when available.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A SHALL use repaired/high-fidelity table evidence when exact table values are requested.
- `knowledge-base-retrieval-maintenance`: The maintenance center SHALL detect low-quality table parses and provide a repair action.

## Impact

- Affects PDF structured parsing, parser configuration, maintenance recommendations/actions, table evidence metadata, and current-paper Q&A retrieval.
- No database migration; cell structures and repair metadata are stored in existing `Paper.metadata_json`.
- Optional external parser command is disabled by default and uses existing subprocess environment/mirror handling.
