## Context

Investigation of the OMTG paper showed:
- The paper has full text and cached structured PDF metadata.
- Cached metadata contains 41 structured blocks, including 16 tables and 25 captions.
- Several tables are low fidelity: headers become generic `Column 1`, rows are partially empty, and figure-like layout text is mistaken for tables.
- `PaperChunkService.retrieve_evidence()` combines structured and document candidates for normal retrieval, but when a query triggers requested-section retrieval, it filters to section candidates only. Structured table blocks do not have section labels, so they are dropped.

Related project patterns:
- RAGFlow treats document parser choice and chunk visibility as operational controls, and combines multiple retrieval signals before ranking answer evidence.
- Docling focuses on document structure conversion with Markdown/JSON outputs, including tables and provenance, making it a stronger backend than raw `pdfplumber` for table-heavy PDFs.
- MinerU is designed for PDF layout understanding and structured Markdown/JSON extraction, including formulas and tables.
- Marker converts PDFs to Markdown/JSON/HTML and uses optional LLM correction for tables/forms/equations when high fidelity matters.

## Goals / Non-Goals

**Goals:**
- Improve actual table parsing quality where better parsers are available.
- Detect and expose low-quality table parse results instead of marking them as fully reliable.
- Ensure table-like questions retrieve table/caption evidence as a separate guaranteed evidence lane.
- Preserve current full-text section retrieval, but merge table evidence back into the final context.

**Non-Goals:**
- Build a full visual table OCR model in this change.
- Require paid third-party parsing services.
- Rewrite all paper retrieval into a vector database pipeline.

## Decisions

1. Prefer advanced parser output for table-heavy PDFs.
   - Rationale: pdfplumber is useful as a fallback, but table fidelity is inconsistent on complex academic layouts.
   - Implementation direction: use the existing `docling`/`command` parser plumbing, improve normalization, and add quality scoring.

2. Add parser quality metadata.
   - Rationale: "ready=true" is not enough; a parse with generic columns and blank rows should be visible as low quality.
   - Quality signals: table block count, generic header count, empty-cell ratio, average table row count, parser backend, and warning strings.

3. Use a dedicated structured-evidence lane for table-like questions.
   - Rationale: table evidence should not compete only through generic BM25 and should not be dropped by section-first filtering.
   - Query triggers: table, 表格, benchmark, baseline, metric/指标, reward, ablation, result/结果, C-Acc, EtF1, tIoU, Gemini, Seed.

4. Merge evidence with diversity constraints.
   - Rationale: current top 4 can be consumed by redundant text. Final evidence should reserve room for table/caption snippets when relevant while retaining section text.

## Risks / Trade-offs

- [Risk] Docling or external parsers may be heavy. -> Keep fallback and make parser backend configurable.
- [Risk] Parser quality scoring is heuristic. -> Use it as operational metadata and tests, not as a hard correctness claim.
- [Risk] More evidence increases prompt size. -> Keep bounded table evidence counts and preserve top-k limits.
