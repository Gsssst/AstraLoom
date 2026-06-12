## Context

The current paper Q&A path builds answer context from paper metadata, extracted full text, page-aware text chunks, and structured table/caption blocks. That path is useful for textual questions but weak for method diagrams, charts, architecture figures, and low-quality table extraction. The old visual asset path was removed because it coupled page rendering, guessed captions, optional summaries, image routes, and UI actions without a clean evidence lifecycle.

The repository already has useful primitives to build on:

- `StructuredPdfExtraction` stores bounded parser blocks in `Paper.metadata_json`.
- `PaperChunkService.retrieve_evidence()` accepts structured blocks and already builds table evidence packs.
- Paper Q&A streams references and evidence metadata that the frontend can render and use to jump to PDF pages.
- Chat supports image attachments for OpenAI-compatible models, but uploaded PDFs are currently reduced to plain text.

External project review points to a parser-first design. Docling is the best default locator because it can expose typed document objects and markdown/table exports when installed. MinerU and PaddleOCR/PP-Structure are better treated as optional high-resource or Chinese/OCR adapters. A vision-capable LLM is valuable for crop-level OCR and visual understanding, but should not be the default whole-PDF parser because whole-page model OCR is slower, more expensive, less deterministic for numeric tables, and harder to cite by page/bbox.

## Goals / Non-Goals

**Goals:**

- Define one reusable document visual evidence schema for paper PDFs and uploaded PDFs.
- Locate candidate visual/table regions with deterministic parsers before invoking vision models.
- Analyze only bounded local crops with optional vision-model OCR/understanding.
- Persist ready evidence so Q&A retrieval can reuse it without synchronous long-running PDF analysis.
- Make visual/table evidence references inspectable with page, bbox, caption, asset path, parser, and confidence metadata.
- Preserve honest degraded behavior when visual evidence is missing, stale, or processing.
- Expose readiness and repair actions through existing maintenance workflows.

**Non-Goals:**

- Do not make Marker the default runtime.
- Do not require Docling, MinerU, PaddleOCR, or any vision model package/API for application startup.
- Do not send entire PDFs or every page screenshot to a vision model by default.
- Do not guarantee perfect OCR for all scanned PDFs or complex merged table cells in the first implementation.
- Do not store private PDF-derived assets in Git or public static directories.
- Do not replace existing full-text extraction, PDF proxying, or table evidence packs.

## Decisions

1. **Create a versioned document visual evidence payload in metadata.**
   - Store under a new metadata key, for example `document_visual_evidence`.
   - Payload contains `version`, `source_path`, `parsed_at`, `status`, `parser`, `page_count`, `assets`, `blocks`, `limits`, and `last_error`.
   - Each evidence item uses stable fields: `id`, `paper_id` or attachment context, `page`, `bbox`, `kind`, `caption`, `asset_path`, `thumbnail_path`, `parser`, `confidence`, `status`, `text`, `markdown`, `summary`, `key_facts`, and `metadata`.
   - Rationale: existing `pdf_structured_content` can keep text/table parsing intact while visual evidence gets a clearer lifecycle and richer asset metadata.
   - Alternative considered: extend the old `visual` block type inside `pdf_structured_content`. Rejected because old visual placeholders are already filtered from retrieval and lack readiness/crop semantics.

2. **Use a parser-first pipeline with Docling as preferred locator.**
   - Pipeline order: resolve local PDF path, run parser adapter, normalize typed regions, render/crop bounded assets, optionally run vision adapter, persist evidence.
   - Default adapter priority: Docling when available, configured command backend if set, lightweight fallback for captions/tables/page image hints.
   - Optional adapters: MinerU for high-quality document layout/OCR, PaddleOCR/PP-Structure for Chinese OCR and table structure, custom command JSON for deployments with their own parser.
   - Rationale: deterministic parser output gives page/bbox/caption evidence that can be cached and cited.
   - Alternative considered: direct whole-PDF vision-model OCR. Rejected as default because cost, latency, numeric reliability, and citation traceability are worse.

3. **Run vision-model OCR only on selected crops.**
   - Candidate crops include figure regions, chart regions, architecture diagrams, table regions with low parser confidence, and pages/captions matching method or experiment terms.
   - The adapter must return strict bounded JSON rather than prose-only output.
   - The output is stored as `ocr_text`, `markdown`, `summary`, `key_facts`, `confidence`, and `model/provider` metadata.
   - Rationale: this uses LLM visual ability where it adds value while preserving parser grounding.
   - Alternative considered: keep assets without summaries. Useful as a fallback, but Q&A still needs text/markdown summaries to retrieve relevant visual evidence.

4. **Keep extraction asynchronous and ready-gated.**
   - User-triggered maintenance and background jobs enqueue bounded batches.
   - Paper Q&A may lazily start extraction if metadata is missing, but it must not block answer generation waiting for long visual parsing.
   - Q&A retrieval only consumes evidence with `status=ready` and non-empty text/markdown/summary or a usable asset reference.
   - Rationale: avoids making chat requests slow or brittle.

5. **Add a visual evidence lane to retrieval instead of mixing all blocks blindly.**
   - Method/figure/chart/architecture queries rank visual evidence and captions before text fallback.
   - Experiment/table queries combine table packs, visual table evidence, captions, and page text.
   - If the question appears visual and no ready evidence exists, system prompts must disclose the gap.
   - Rationale: precise routing prevents stale placeholders from being treated as visual understanding.

6. **Reuse frontend reference metadata before adding heavy UI.**
   - Paper answer references already render tags and navigate to pages.
   - Add preview card support only when `asset_path` or `thumbnail_path` exists.
   - Use page/bbox metadata to navigate to the PDF page first; bbox highlighting can be a later enhancement.
   - Rationale: keeps the first implementation focused on evidence correctness.

7. **Share the pipeline with chat PDF uploads.**
   - Uploaded PDFs should use the same parser and evidence schema, scoped to the chat attachment instead of a persisted paper record.
   - The first implementation can persist attachment evidence in message references or a bounded temporary artifact store.
   - Rationale: the user explicitly needs both chat and paper-page Q&A to answer from tables/images.

## Risks / Trade-offs

- [Risk] Optional parsers or vision models are unavailable in local deployments. -> Keep dynamic imports/configured command adapters and return readiness states instead of hard failures.
- [Risk] Vision-model OCR may hallucinate or misread numbers. -> Require strict JSON, preserve parser/table evidence alongside model output, store confidence, and instruct Q&A to avoid unsupported numeric claims.
- [Risk] Cropping regions can be wrong. -> Keep page-level fallback assets and include parser/crop strategy metadata for inspection.
- [Risk] Asset files can grow quickly. -> Enforce per-paper page, crop, byte, and model-call limits; reuse cached assets by source path and version.
- [Risk] Synchronous Q&A could trigger expensive work. -> Start extraction opportunistically but answer only from ready evidence.
- [Risk] Historical metadata from removed visual implementations may exist. -> Ignore old visual keys unless migrated into the new versioned schema by a bounded maintenance action.
- [Risk] Uploaded PDF evidence may include private data. -> Store assets under existing private upload/cache paths and require authenticated access through API routes.

## Migration Plan

1. Add the new schema and readers while continuing to ignore historical visual metadata.
2. Implement parser normalization and crop generation behind feature/config checks.
3. Add maintenance endpoints and jobs for bounded backfill.
4. Add Q&A retrieval lane and prompt guardrails for ready/missing visual evidence.
5. Add frontend readiness indicators and preview-ready references.
6. Enable chat PDF uploads to call the shared pipeline for bounded evidence extraction.
7. Rollback by disabling parser/vision adapters and falling back to text/table evidence; persisted visual evidence can remain unused.

## Open Questions

- Which vision provider/model should be the first supported crop OCR adapter in production: OpenAI-compatible vision, DeepSeek vision if available, or a deployment-supplied command?
- Should uploaded PDF visual evidence persist beyond the chat session or expire with temporary upload cleanup?
- Should bbox highlighting in the PDF viewer be part of the first implementation or follow after page navigation and preview cards are stable?
