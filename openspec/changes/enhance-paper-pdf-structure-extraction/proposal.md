## Why

Paper AI currently relies on plain PDF text extraction, so questions whose answers live in tables, figure captions, page images, or layout-dependent content often have no retrievable evidence. GitHub references such as Unstructured, Marker, Docling, and MinerU all point to the same pattern: convert PDFs into LLM-ready structured Markdown/JSON with tables, images, captions, page metadata, and reading order before retrieval.

## What Changes

- Extract page-aware structured PDF content in addition to plain text.
- Convert detected PDF tables into Markdown table blocks so experiment results and ablations can be retrieved.
- Capture figure/table captions and image placeholders as evidence blocks with page numbers.
- Include structured evidence blocks in paper Q&A retrieval and evidence references.
- Persist structured extraction summaries in paper metadata so repeated questions do not repeatedly parse the same PDF.
- Keep the current plain-text fallback when structured parsing is unavailable or incomplete.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Paper AI evidence retrieval is updated to include structured PDF table, caption, and visual-placeholder evidence, not only extracted prose text.

## Impact

- Affects `backend/app/services/report_service.py`, `backend/app/services/memory_service.py`, and `backend/app/services/paper_chunk_service.py`.
- Adds targeted backend tests for table/caption extraction and structured evidence retrieval.
- Stores structured extraction metadata under `Paper.metadata_json`; no database migration is required.
- No new heavyweight OCR/VLM dependency is added in this iteration.
