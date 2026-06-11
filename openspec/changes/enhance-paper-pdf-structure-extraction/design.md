## Context

The current paper Q&A path extracts PDF content as plain text through `pdfplumber.extract_text()` with a `fitz.get_text()` fallback. This misses or flattens important evidence from academic PDFs, especially experiment tables, ablation matrices, figure captions, and image-only content. The retrieval layer then chunks only `paper.full_text`, so the model correctly refuses to answer when relevant evidence is absent.

GitHub reference check:
- Docling advertises advanced PDF understanding with page layout, reading order, table structure, formulas, image classification, OCR, Markdown export, and JSON export.
- MinerU converts PDFs and images into Markdown/JSON, preserves reading order, extracts images, image descriptions, tables, table titles, footnotes, and formulas, and supports OCR/VLM backends for harder documents.
- Unstructured and Marker follow the same broad pattern: partition/convert documents into structured LLM-ready elements rather than treating a PDF as one plain text stream.

## Goals / Non-Goals

**Goals:**
- Improve paper Q&A grounding for table-heavy and figure-caption questions.
- Preserve page numbers and evidence type for structured PDF blocks.
- Reuse installed PDF parsers first, without adding a heavyweight OCR/VLM dependency in this change.
- Cache structured extraction results in existing paper metadata.
- Keep plain-text fallback behavior intact.

**Non-Goals:**
- Full chart understanding or visual reasoning over plots.
- OCR for scanned PDFs.
- Formula recognition into LaTeX.
- Installing Docling, MinerU, Marker, or Unstructured as production dependencies in this iteration.
- Adding a new database table or migration.

## Decisions

1. Add a light structured extraction layer around `pdfplumber` and `fitz`.
   - Rationale: `pdfplumber` is already installed and can extract page tables and page text; `fitz` can detect page images when available. This gives immediate gains without deployment risk.
   - Alternative considered: install Docling/MinerU. Rejected for this iteration because they bring larger model/runtime requirements and should be evaluated as a separate parser backend later.

2. Store structured extraction under `Paper.metadata_json["pdf_structured_content"]`.
   - Rationale: The paper table already has JSON metadata and the structured content is derived/cacheable data. This avoids a migration while preserving room for future schema evolution.
   - Alternative considered: add a new `paper_pdf_blocks` table. Rejected until we need block-level embedding, indexing, or UI inspection.

3. Convert tables into Markdown-like evidence blocks and feed them into the existing chunk retriever.
   - Rationale: Markdown tables are compact, LLM-readable, and work with the current BM25 retriever.
   - Alternative considered: keep raw cell arrays only. Rejected because raw arrays are less useful in prompt context.

4. Represent images as visual placeholders with page number and nearby captions when available.
   - Rationale: Without OCR/VLM we cannot honestly claim to understand image pixels, but the system can tell the model that a figure exists and provide caption text as evidence.
   - Alternative considered: ignore image pages until OCR exists. Rejected because figure captions often answer user questions and image existence helps explain remaining limitations.

## Risks / Trade-offs

- Table extraction quality varies across PDFs -> Keep plain text fallback and mark evidence as `table` so users can see its source type.
- Image placeholders can be overinterpreted by the model -> Prompt text explicitly states that visual placeholders are not pixel-level analysis.
- Metadata JSON can grow for large PDFs -> Store capped structured Markdown and a bounded number of visual blocks.
- Existing papers already have only `full_text` cached -> Structured content is generated lazily from `pdf_path` when paper Q&A needs it.
