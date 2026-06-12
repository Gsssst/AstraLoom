## Context

The project already has a strong text-first evidence pipeline:

- `report_service` can extract captions, table markdown, Docling blocks, and optional repaired tables.
- `paper_chunk_service` can route Introduction/Method/Experiment/Table questions to text, tables, and evidence packs.
- `memory_service` converts retrieved evidence into paper Q&A context and structured metadata.

The missing layer is true visual evidence. The current lightweight parser only records a `visual` placeholder when embedded images exist, explicitly saying that no pixel-level analysis has been performed. That is why method diagrams, charts, result plots, and scanned tables remain invisible to the model.

External project lessons:

- Docling (`docling-project/docling`) is a good structural parser foundation for layout, tables, pictures, formulas, and OCR.
- Marker (`datalab-to/marker`) is useful as a high-fidelity table adapter and optional parser command.
- ColPali/Byaldi (`illuin-tech/colpali`, `AnswerDotAI/byaldi`) show a stronger long-term path: retrieve visually relevant PDF pages directly rather than relying only on OCR/text.
- VARAG-style systems keep text RAG, vision RAG, and ColPali-like page retrieval as complementary lanes.

## Goals / Non-Goals

**Goals:**

- Extract reusable visual assets from PDFs: page previews and likely figure/table regions.
- Persist assets in existing paper metadata first, avoiding a large migration in this initial slice.
- Generate optional visual summaries with the active LLM provider when image input is supported.
- Feed visual summaries into the existing evidence retrieval pipeline.
- Include visual evidence references in paper Q&A responses with page, bbox, asset path, caption, and modality metadata.
- Surface missing visual assets/summaries in maintenance health.

**Non-Goals:**

- Do not require GPU, ColPali, or Byaldi for first release.
- Do not build a full vector index for images yet.
- Do not guarantee exact chart numeric extraction from arbitrary plots.
- Do not replace text/table RAG; visual evidence augments it.

## Decisions

1. Persist visual assets under `Paper.metadata_json`.
   - Key: `pdf_visual_assets_v1`.
   - Rationale: existing structured PDF metadata already follows this pattern; first release avoids a database migration and keeps rollback simple.
   - Alternative considered: a dedicated `paper_visual_assets` table. Better for large-scale indexing, but premature before the extraction/summarization contract stabilizes.

2. Extract page images and heuristic figure/table crops with PyMuPDF.
   - Page preview: render each page at a bounded zoom.
   - Region assets: use caption/structured metadata and embedded image rectangles when available; fall back to page-level visual assets.
   - Rationale: PyMuPDF is already used, and page-level assets provide reliable coverage even when bbox detection is imperfect.

3. Use optional VLM summaries, not mandatory online image calls.
   - If the active provider supports image content and keys are configured, summarize selected assets.
   - Otherwise store unsummarized assets and expose “visual summaries missing” maintenance actions.
   - Rationale: deployments vary; text-only systems should still benefit from page/asset references and future summarization.

4. Add a visual evidence lane to retrieval.
   - Visual assets become `EvidenceChunk` candidates with source types such as `visual_asset`, `visual_summary`, and `visual_pack`.
   - Figure/chart/architecture/method/experiment questions prefer this lane while still merging text/table evidence.
   - Rationale: avoids duplicating an entire retrieval stack and keeps Q&A behavior consistent.

5. Keep ColPali/Byaldi as a future backend boundary.
   - Design the metadata and evidence shape so a later visual page retriever can emit the same asset refs.
   - Rationale: visual page retrieval is attractive but adds model downloads, GPU pressure, and a separate index lifecycle.

## Risks / Trade-offs

- [Risk] Heuristic crops miss a figure or crop too broadly. -> Always include page-level visual assets and captions so answers can still cite the page.
- [Risk] VLM summaries hallucinate visual content. -> Store prompts, mark summaries as generated, and require answers to cite asset/page references rather than treating summaries as ground truth alone.
- [Risk] Metadata JSON grows too large. -> Bound page count, image resolution, summary length, and asset count; move to a table/index in a later change if needed.
- [Risk] Some providers do not support image input. -> Keep summarization optional and show clear text-only/missing-visual warnings.
- [Risk] Extra parsing increases latency. -> Run visual extraction through explicit maintenance actions and lazy parse only when bounded.

## Migration Plan

1. Add configuration defaults for visual extraction and summarization limits.
2. Add visual asset extraction service writing files under `uploads/paper-visual-assets/<paper-id>/`.
3. Persist `pdf_visual_assets_v1` metadata on parse/maintenance.
4. Extend retrieval and paper Q&A context to include visual assets.
5. Add API status fields and maintenance actions.
6. Add frontend visual evidence cards.

Rollback: remove the metadata key and uploaded visual asset directory; text/table retrieval remains unchanged.
