## Why

Paper-detail Q&A and chat PDF upload currently ground answers mostly in extracted plain text plus limited table/caption blocks. Users who ask about methods, architecture diagrams, charts, ablation tables, or experimental results need evidence from figures and tables, but the previous visual-asset implementation was removed because it mixed expensive rendering, guessing, and UI surface without a clean evidence contract.

This change rebuilds multimodal PDF support as a document visual evidence pipeline: deterministic parsers first locate page regions and captions, optional vision-model adapters analyze only bounded crops, and Q&A consumes persisted ready evidence instead of inferring from unseen PDF images.

## What Changes

- Introduce a shared document visual evidence pipeline for local/cacheable PDFs.
- Normalize parser output into a single bounded evidence schema containing page, bbox, kind, caption, asset path, parser, confidence, text/markdown/summary, and status metadata.
- Use Docling as the default parser/locator when available, keep existing lightweight parsing as fallback, and allow MinerU, PaddleOCR/PP-Structure, or command adapters as optional parser backends.
- Add an optional vision-model OCR/understanding adapter that analyzes selected crops only, not whole PDFs by default.
- Persist visual/table evidence so paper Q&A and uploaded-PDF chat can reuse it without rerunning expensive parsing during answer generation.
- Route method, figure, chart, architecture, table, and experiment questions through visual/table evidence lanes only when evidence is ready.
- Preserve honest degraded behavior: if visual evidence is unavailable or still processing, the assistant must disclose that limitation rather than describe unseen figures or charts.
- Surface visual-evidence readiness and repair actions through the existing maintenance center with bounded asynchronous jobs.

## Capabilities

### New Capabilities

- `document-visual-evidence-pipeline`: Shared backend contract for parsing PDFs into page-aware visual/table evidence assets, optional crop-level vision-model OCR, readiness metadata, and reuse by paper Q&A and chat PDF attachments.

### Modified Capabilities

- `paper-multimodal-visual-evidence`: Replace the old visual asset assumptions with the new parser-first, crop-level visual evidence pipeline and ready-gated retrieval.
- `visual-evidence-crops`: Require crop generation to be tied to parser-detected regions/captions and to expose preview-ready asset references.
- `paper-qa-evidence-grounding`: Require paper Q&A to use ready visual/table evidence for method and experiment questions, and to disclose visual evidence gaps.
- `knowledge-base-retrieval-maintenance`: Add visual-evidence readiness and bounded backfill actions to retrieval maintenance health.
- `paper-library-maintenance-center`: Show visual/table evidence readiness in paper processing status and privileged repair actions.

## Impact

- Backend services: PDF structured parsing, visual evidence extraction, paper Q&A context construction, chat PDF upload processing, maintenance jobs, parser runtime health, and asset serving.
- Data model: paper metadata JSON gains a versioned document visual evidence payload; optional durable asset paths point to local generated crops/thumbnails that must not be committed.
- APIs: paper detail, maintenance, paper Q&A, and chat upload responses expose visual evidence readiness and references without breaking existing text/table evidence fields.
- Frontend: paper detail answer references can show visual evidence preview cards and navigate to PDF pages; maintenance views show visual evidence status and bounded repair actions.
- Dependencies: Docling remains optional/default-if-installed; MinerU, PaddleOCR/PP-Structure, and vision-model OCR remain optional adapters configured per deployment.
