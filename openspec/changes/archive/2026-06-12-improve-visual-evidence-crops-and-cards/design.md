## Context

The current visual evidence implementation renders bounded PDF pages and links caption-derived figure/table assets back to the full page image. This gives paper Q&A a multimodal lane, but the UI cannot show a focused evidence preview and the model/reader cannot distinguish whether an answer is based on a figure/table region or a broad page screenshot.

## Goals / Non-Goals

**Goals:**

- Generate separate region crops for caption-linked figure/table assets when possible.
- Store bbox/crop metadata that can later be replaced by a real layout detector without changing API shape.
- Display visual evidence references as preview cards in the paper Q&A panel.
- Keep page-level renders as robust fallback evidence.

**Non-Goals:**

- Introduce a heavyweight layout-model dependency in this iteration.
- Guarantee exact figure/table boundaries for every PDF layout.
- Replace OCR/table parsing or the existing structured text retrieval lane.

## Decisions

- Use PyMuPDF clipping for crops. The project already depends on PyMuPDF for PDF rendering, so region crops can be generated without new infrastructure.
- Use deterministic caption-page region heuristics. Until a layout detector is introduced, figure captions crop a broad upper/central page region and table captions crop a broad middle/lower region. The crop stores `crop_strategy` so later detectors can supersede it.
- Store crop images as the caption asset `image_path`. Existing image-serving endpoints can then serve focused crops without adding another API endpoint.
- Render preview cards only for visual references with an `asset_id`. Non-visual references continue using compact tags.

## Risks / Trade-offs

- Heuristic crops may include extra surrounding content. → The metadata marks the crop as heuristic and keeps page assets available as fallback.
- Some PDFs use caption placement that differs from the heuristic. → The design is intentionally compatible with future bbox detectors and parser-provided coordinates.
- Image previews could clutter long answers. → Cards are compact and only appear for visual evidence references.
