## Why

The current structured PDF extraction improves tables and captions with installed lightweight parsers, but it still cannot consume richer OCR/VLM parser output from tools like Docling, MinerU, Marker, or Unstructured. Those GitHub projects expose the next step for paper Q&A: parse PDFs into Markdown/JSON blocks with reading order, OCR, tables, formulas, and image descriptions before retrieval.

## What Changes

- Add a configurable advanced structured PDF parser backend interface.
- Support a generic command backend that can call a local parser and read its JSON output without hard-coding one heavy dependency.
- Normalize external parser output into the existing structured PDF metadata and evidence blocks.
- Forward HuggingFace mirror/cache environment variables to parser subprocesses so Docling/MinerU-style model downloads use the configured mirror.
- Keep the current lightweight `pdfplumber`/`fitz` parser as the default and fallback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Structured paper evidence can come from a configured advanced parser backend and falls back to the lightweight parser.
- `deployment-readiness`: Deployments can configure an advanced PDF parser command and the parser inherits configured runtime model mirror/cache settings.

## Impact

- Affects backend configuration, PDF structured extraction, and paper Q&A retrieval.
- Adds tests for external parser payload normalization, command fallback, and HuggingFace mirror environment propagation.
- No new required dependency and no database migration.
