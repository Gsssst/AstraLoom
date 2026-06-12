## 1. Evidence Schema And Storage

- [ ] 1.1 Add versioned document visual evidence metadata helpers for papers, including status, limits, parser health, asset records, and last error handling.
- [ ] 1.2 Define normalized evidence item builders for figure, chart, table, page render, OCR, formula, caption, and visual table evidence.
- [ ] 1.3 Add private asset path utilities for generated crops/thumbnails that keep PDF-derived images outside Git-tracked public assets.
- [ ] 1.4 Add tests for schema normalization, bounds enforcement, stale source-path detection, and old visual metadata ignoring.

## 2. Parser And Crop Pipeline

- [ ] 2.1 Extend the Docling adapter normalization to capture page, bbox, picture/figure/table/caption/formula candidates when available.
- [ ] 2.2 Add a parser orchestration service that resolves local PDFs, runs configured parser adapters, and persists visual evidence status without blocking the event loop.
- [ ] 2.3 Add PDF render/crop generation for parser-detected regions with page-level fallback assets and crop strategy metadata.
- [ ] 2.4 Add optional command/MinerU/PaddleOCR-compatible JSON normalization hooks through the shared schema.
- [ ] 2.5 Add tests for Docling-shaped visual regions, command-parser visual/table payloads, crop fallback behavior, and parser failure recovery.

## 3. Vision Adapter

- [ ] 3.1 Add a crop-level vision adapter interface that accepts bounded image crops and returns strict JSON for OCR text, table markdown, visual summary, key facts, confidence, and model metadata.
- [ ] 3.2 Wire an OpenAI-compatible vision provider path when configured, with text fallback when no image-capable provider is available.
- [ ] 3.3 Enforce per-paper crop and model-call limits so visual extraction cannot analyze whole PDFs by default.
- [ ] 3.4 Add tests for strict JSON parsing, malformed model output fallback, unavailable vision provider status, and numeric/table confidence metadata.

## 4. Async Jobs And Maintenance APIs

- [ ] 4.1 Add bounded backend functions/endpoints for extracting visual evidence for one paper and for batch backfill.
- [ ] 4.2 Add asynchronous job status reporting for queued/running/success/failed visual evidence maintenance work.
- [ ] 4.3 Extend maintenance health and processing status responses with visual evidence readiness, failed extraction samples, missing summary/OCR counts, and low-confidence table evidence.
- [ ] 4.4 Add tests for admin authorization, bounded batch counts, retrying failed visual extraction, and route ordering safety.

## 5. Q&A Retrieval And Prompt Guardrails

- [ ] 5.1 Extend paper evidence retrieval to include ready visual evidence items while still filtering historical placeholder visual blocks.
- [ ] 5.2 Add visual/table routing for method, architecture, figure, chart, table, and broad experiment questions.
- [ ] 5.3 Add prompt guardrails and evidence metadata for visual missing, visual processing, and visual extraction failed states.
- [ ] 5.4 Ensure streamed and non-streamed paper Q&A return visual evidence references with page, bbox, asset path, caption, parser, confidence, and snippets.
- [ ] 5.5 Add tests for visual evidence selection, visual insufficiency disclosure, experiment table crop evidence, and current-paper evidence metadata.

## 6. Chat PDF Upload Reuse

- [ ] 6.1 Route chat PDF uploads through the shared document visual evidence pipeline after text extraction, using attachment-scoped evidence metadata.
- [ ] 6.2 Include ready uploaded-PDF visual/table evidence in chat context and message references without rerunning extraction on later turns.
- [ ] 6.3 Add degraded instructions when uploaded PDFs only have plain text extraction or visual evidence processing failed.
- [ ] 6.4 Add tests for PDF upload with table/figure evidence, text-only fallback, and private attachment asset access.

## 7. Frontend Evidence Experience

- [ ] 7.1 Update paper detail chat references to render preview-ready visual evidence cards when thumbnail or asset metadata is available.
- [ ] 7.2 Preserve existing reference-chip page navigation and include visual kind, confidence, caption, and OCR/summary snippet in tooltips/cards.
- [ ] 7.3 Update maintenance views to show visual evidence readiness and admin-only visual extraction/backfill actions.
- [ ] 7.4 Add frontend tests or contract tests for visual reference rendering, PDF page navigation, and non-admin maintenance visibility.

## 8. Verification

- [ ] 8.1 Run OpenSpec validation for `add-document-visual-evidence-pipeline`.
- [ ] 8.2 Run targeted backend tests for report service, paper chunk retrieval, paper Q&A, chat upload, and maintenance endpoints.
- [ ] 8.3 Run frontend build or targeted frontend tests for paper detail and maintenance UI changes.
- [ ] 8.4 Manually verify a local paper Q&A flow: visual evidence missing disclosure, visual extraction completion, and answer references using ready visual/table evidence.
