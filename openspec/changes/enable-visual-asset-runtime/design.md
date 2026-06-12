## Context

The archived visual evidence changes added a practical first slice for multimodal paper Q&A:

- render bounded PDF pages as visual assets;
- create broad caption-linked figure/table crops;
- persist metadata under `pdf_visual_assets_v1`;
- feed visual assets and summaries into the existing evidence retrieval lane;
- show visual evidence references as frontend preview cards.

That implementation assumes PyMuPDF is available, but the current backend image only declares `pdfplumber` and `pikepdf`. Runtime health reports `fitz: False`, so extraction records a failure instead of creating assets.

GitHub references checked before implementation:

- `pymupdf/PyMuPDF`: established Python binding for MuPDF, commonly used to open PDFs, render pages to pixmaps, and save images.
- `AnswerDotAI/byaldi` / ColPali-style projects: stronger long-term visual document retrieval retrieves PDF pages directly, but that requires a heavier model/index lifecycle and is out of scope for this runtime fix.

## Decisions

1. Add PyMuPDF to the main backend requirements.
   - Rationale: `paper_visual_service` and existing PDF fallbacks import `fitz` directly; optional fallback behavior is already coded, but visual assets require rendering to be useful.
   - Alternative considered: move visual extraction to Marker or an external command. Rejected for this fix because the current implementation is already PyMuPDF-based and needs the smallest operational repair.

2. Keep visual summary generation disabled by default.
   - Rationale: rendering image assets is deterministic and local; VLM summarization depends on provider support and cost.

3. Verify with a generated one-page PDF instead of relying on external papers.
   - Rationale: the test should prove the runtime can render a real PDF without network or fixture fragility.

4. Treat async visual maintenance as a follow-up.
   - Rationale: batch visual extraction may become slow, but the immediate blocker is missing runtime dependency. Once extraction works, we can reuse the table-repair job pattern if users hit UI timeouts.

## Risks / Trade-offs

- PyMuPDF increases the backend image size. The benefit is direct local rendering with no GPU or external service dependency.
- Heuristic crops remain broad and may not isolate exact figure boundaries. The existing metadata records crop strategy and keeps page-level fallbacks.
- If the container is not rebuilt after changing requirements, health will still report `fitz: False`. Verification must include the running backend environment.

## Rollout

1. Add PyMuPDF dependency.
2. Reinstall/rebuild backend dependencies.
3. Run runtime health verification until `fitz: True`.
4. Run visual asset extraction tests against a real generated PDF.
