## Context

Document visual evidence is stored in `paper.metadata_json.document_visual_evidence.items`. Each item has an original parser `kind`, optional model-derived `metadata.vision_elements`, and optional `metadata.vision_corrected_kind`.

Readiness currently counts `missing_ocr_count` from `visual_evidence_effective_kind(item) in {"table", "visual_table"} and not item.markdown`. This works for true tables but misfires when a parser/caption candidate is stored as `kind=table` while the vision pass identified the page/crop as a figure or text-only page with no visible table.

## Goals / Non-Goals

**Goals:**

- Prevent text/figure items corrected by vision output from being counted as missing table OCR.
- Support already cached metadata where `vision_corrected_kind` was not written but `vision_elements` show no table evidence.
- Preserve true table missing-OCR signals when a table is visible but markdown is absent.

**Non-Goals:**

- Adding a new OCR model or changing model prompts.
- Re-cropping table regions or implementing precise table bbox localization.
- Changing the frontend layout for processing labels beyond the corrected counts.

## Decisions

- Infer effective kind from vision elements before original parser kind.
  - Rationale: the vision model has pixel/page evidence and can overrule parser text/caption heuristics.
  - Alternative considered: require a full reparse to populate `vision_corrected_kind`; rejected because existing cached results already contain enough evidence and should be fixed without manual backfill.

- Treat table candidates with no table vision element as the first non-table vision element when present.
  - Rationale: if the model returns `figure` or `text` and explicitly no `table`, the item should not block table OCR readiness.
  - Alternative considered: count them as a new "table location missing" failure; rejected for this fix because the user-facing failure currently blocks processing even though no table is visible in that item.

- Keep true table candidates without markdown counted as missing OCR.
  - Rationale: real visual table gaps must remain visible for maintenance and Q&A grounding quality.

## Risks / Trade-offs

- A model could mistakenly classify a visible table as text, causing an OCR gap to be hidden.
  - Mitigation: only apply non-table correction when vision elements contain no table-like element, and keep regression tests for true table/no-markdown cases.

- Some old metadata may have raw OCR text that mentions table content but no structured markdown.
  - Mitigation: this change does not treat text as table-complete; it only removes false table status when the visual evidence says the item is not a table.
