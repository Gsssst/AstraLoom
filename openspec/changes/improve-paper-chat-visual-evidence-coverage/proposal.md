## Why

Paper-page Q&A currently treats broad visual questions like "有没有可视化结果" as a normal top-k visual retrieval problem. That can return only a few high-scoring candidates, so the model may miss later figures and incorrectly imply that a visual result cannot be located.

## What Changes

- Add a broad visual evidence catalog path for paper Q&A questions asking for available figures, visualizations, qualitative cases, or what visual results support.
- Return compact page-aware figure/visual metadata before the normal top-k text fallback so the model can enumerate all available visual evidence even when only a bounded number of image crops are attached.
- Make visual answer guidance distinguish between "metadata/caption is available" and "image pixels were attached and inspected".
- Keep the existing single-figure and table-specific retrieval behavior for targeted questions.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Broad visual result questions require catalog-style evidence coverage instead of only top-k visual snippets.
- `paper-multimodal-visual-evidence`: Visual retrieval must expose coverage metadata for all available figures/visual assets, while still bounding attached images.

## Impact

- Backend retrieval planning and visual evidence ranking in `backend/app/services/paper_chunk_service.py`.
- Paper Q&A context/guidance and image attachment metadata in `backend/app/api/papers.py` and `backend/app/services/memory_service.py`.
- Focused backend tests for broad visual-query planning and visual catalog retrieval.
