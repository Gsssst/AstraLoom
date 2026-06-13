## Context

The current visual evidence pipeline creates candidate items from structured parser blocks. Those candidates can be wrong: a block labeled as a table may correspond to a figure page, algorithm page, or body text that references a table. The vision OCR adapter can correctly identify these cases, but readiness still uses the original `item.kind` and therefore counts them as missing table OCR when no markdown is returned.

There is a second operational issue: old visual evidence payloads can contain `metadata.asset_error = "fitz unavailable: No module named 'fitz'"`. Once the worker has `fitz`, force re-extraction should replace those items with rendered assets and clear the blocking error.

## Goals / Non-Goals

Goals:

- Count a visual evidence item by the effective kind after OCR, not only the parser kind.
- Consider a parser-table candidate complete when OCR returns a ready non-table visual/text element with OCR text or summary.
- Keep real tables strict: actual table items still need markdown to count as table OCR complete.
- Let forced re-extraction replace stale asset-error payloads.
- Keep status behavior shared between manual extraction and background reconciliation.

Non-goals:

- Add a new OCR provider or UI control.
- Relax actual table OCR quality requirements.
- Change paper Q&A retrieval strategy.

## Decisions

1. Derive an effective kind from vision metadata.
   - If `metadata.vision_elements[0].type` normalizes to `figure`, `chart`, `diagram`, `image`, or `text`, the item should no longer be treated as a table for missing table markdown counts.
   - If the vision element type remains `table`, the item remains a table and still requires markdown.

2. Promote model-corrected kinds onto persisted metadata.
   - Store `metadata.vision_corrected_kind` and `metadata.parser_kind` when OCR result type disagrees with parser kind.
   - Keep `item.kind` stable for compatibility, but use the effective kind in status and block conversion.

3. Classify corrected text-only pages as complete evidence when they have OCR text or summary.
   - This prevents a page that only mentions "Table 5" from forcing a markdown table requirement.

4. Preserve force re-extraction semantics.
   - Existing `ensure_document_visual_evidence(..., force=True)` reparses and re-renders from the PDF path. The fix should make tests assert that stale asset errors are cleared by a successful forced run rather than adding a separate cleanup path.

## Risks / Trade-offs

- Risk: A model could incorrectly call a real table "text". Mitigation: keep confidence, OCR text, summary, and vision metadata visible to downstream evidence, and only relax the markdown requirement when the model returns a ready non-table element.
- Risk: Existing UI labels may still show item counts from parser candidates. Mitigation: status fields will report counts using effective kind while preserving total item count.
