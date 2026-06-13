## Context

The current document visual evidence pipeline renders page images and creates table visual evidence items, but a previous conservative model-call budget meant table items could keep only parser-derived markdown. For OMTG, the rendered page images contain complete tables, while `pdfplumber` misses full table boundaries and headers.

The existing model adapter already accepts image paths and returns strict JSON with table markdown, OCR text, key facts, confidence, and uncertainty fields. The missing behavior is deciding which table assets deserve OCR, applying OCR when budget allows, and preferring the OCR output in Q&A.

## Goals / Non-Goals

**Goals:**

- OCR all table-like visual evidence when parser markdown is missing, generic, sparse, or otherwise low fidelity.
- Use the existing system LLM provider/model path; no extra user-visible vision configuration or status.
- Preserve async processing and avoid sending whole PDFs.
- Make Chinese experiment-analysis questions trigger the complete experiment evidence pack.
- Keep table images hidden in the chat UI; only evidence markdown/references improve.

**Non-Goals:**

- Add a new external OCR service or required dependency.
- Rewrite PDF table detection from scratch.
- Guarantee perfect table reconstruction for unreadable scans.

## Decisions

1. Enable complete weak-table OCR by default through existing limits.
   - A `PDF_VISUAL_EVIDENCE_MAX_MODEL_CALLS` value of `0` means no per-paper cap, so every weak visual table item with an asset is OCRed and saved. Deployments can still set a positive cap if they need a hard operational limit.

2. Prioritize weak table evidence for OCR.
   - OCR candidates are table items whose markdown is empty, has generic headers, has too few rows, has many empty cells, or comes from a caption/page fallback.
   - This makes OMTG Table 10/13 eligible because they have clear page assets but no markdown.

3. Store OCR output on the existing visual evidence item.
   - `markdown`, `text`, `summary`, `key_facts`, `confidence`, and `metadata.vision_elements` already exist, so no database migration is needed.

4. Treat broad Chinese experiment-analysis terms as `experiment_complete`.
   - Phrases such as "实验分析", "实验结果分析", "分析实验", "结果分析", and "消融分析" should include all ready structured and visual tables within budget.

## Risks / Trade-offs

- [Risk] Page screenshots may contain multiple tables or surrounding text. -> Prompt asks for one element per visible table and preserves uncertainty notes; item caption/page context helps select the relevant table.
- [Risk] More OCR calls can increase cost/latency. -> Run during visual evidence extraction/backfill, not inline in answer generation, and retain an optional positive deployment cap.
- [Risk] OCR markdown can still be uncertain. -> Preserve `uncertain_cells`, confidence, and parser metadata so answers can disclose uncertainty.
