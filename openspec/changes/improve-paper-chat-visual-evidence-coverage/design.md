## Context

Paper Q&A already has structured text, table, formula, and visual evidence lanes. Visual queries currently use a top-k ranking lane, which is appropriate for "解释 Figure 3" but too narrow for "有没有可视化结果/这些结果支持什么结论". Mature multimodal RAG systems handle this by keeping a document-level visual catalog separate from the final bounded image attachments: captions and visual metadata can cover all figures, while only a small number of crops/images are sent to the model for pixel inspection.

## Goals / Non-Goals

**Goals:**
- Detect broad visual survey questions.
- Provide a compact catalog of available figure/visual evidence across the paper before normal text fallback.
- Preserve bounded model payloads by attaching only a limited number of images while telling the model which figures are metadata-only.
- Avoid regressions for targeted figure/table/formula questions.

**Non-Goals:**
- Rebuild the PDF parser or visual extraction pipeline.
- Guarantee pixel-level inspection for every figure in a long paper in one chat turn.
- Add a new external multimodal retrieval dependency.

## Decisions

- Add a `visual_catalog` retrieval strategy for broad visual questions.
  - Rationale: a top-k lane optimizes relevance, while this user intent needs coverage.
  - Alternative considered: simply raise top-k. That increases context size and still may miss low-scoring later figures.
- Build catalog evidence from existing structured visual evidence blocks.
  - Rationale: the extraction pipeline already normalizes page, caption, summary, OCR, bbox, parser source, and asset metadata.
  - Alternative considered: rerun PDF image extraction at answer time. That would slow chat and duplicate existing async extraction.
- Keep image attachments bounded and make attachment state explicit in guidance.
  - Rationale: model providers have payload and latency limits; answer quality improves when the prompt distinguishes caption metadata from inspected pixels.

## Risks / Trade-offs

- [Risk] Long papers can contain many figures, increasing context size. → Mitigation: cap catalog entries and keep each entry compact.
- [Risk] Caption-only catalog entries may not be enough to judge visual details. → Mitigation: require the answer to state whether image pixels were attached/inspected.
- [Risk] Broad visual detection may over-trigger. → Mitigation: require both visual terms and broad/list/support markers, while keeping explicit figure-number questions on the existing targeted lane.
