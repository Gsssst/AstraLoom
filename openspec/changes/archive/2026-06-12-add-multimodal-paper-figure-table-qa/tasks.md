## 1. Visual Asset Foundation

- [x] 1.1 Add configuration defaults for visual asset extraction, render scale, limits, and optional summarization.
- [x] 1.2 Implement a `paper_visual_service` that extracts bounded PDF page visual assets and stores metadata in `Paper.metadata_json`.
- [x] 1.3 Add status helpers for visual asset coverage and missing-summary state.

## 2. Visual Summaries

- [x] 2.1 Add optional image-capable LLM summarization helper that can describe one extracted visual asset.
- [x] 2.2 Persist visual summaries and key facts without failing when no vision model is configured.

## 3. Multimodal Retrieval

- [x] 3.1 Convert visual assets/summaries into `EvidenceChunk` candidates with page, bbox, caption, and asset metadata.
- [x] 3.2 Extend paper evidence retrieval to route figure/chart/method/experiment queries through a visual evidence lane.
- [x] 3.3 Update paper Q&A context warnings so missing visual evidence is transparent.

## 4. APIs and Frontend

- [x] 4.1 Add paper status/API fields and bounded maintenance actions for visual asset extraction and summary backfill.
- [x] 4.2 Show visual evidence references as frontend evidence cards with page/asset metadata.

## 5. Verification

- [x] 5.1 Add backend tests for visual asset metadata normalization and visual evidence retrieval.
- [x] 5.2 Add frontend/contract tests for visual evidence references.
- [x] 5.3 Run OpenSpec validation and targeted backend/frontend checks.
